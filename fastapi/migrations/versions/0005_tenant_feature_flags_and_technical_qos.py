# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0005_tenant_feature_flags_and_technical_qos

Revision ID: 0005_tenant_feature_flags_and_technical_qos
Revises: 0004_ipam_and_field_ops
Create Date: 2026-10-18 22:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_feature_flags_qos"
down_revision: str | None = "0004_ipam_and_field_ops"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. ENUM for SubscriberDeviceStatus
    subscriber_device_status_enum = postgresql.ENUM(
        "PENDING_ACTIVATION",
        "ACTIVE",
        "ISOLATED_ADMINISTRATIVE",
        "SUSPENDED_TECHNICAL",
        "DECOMMISSIONED",
        name="subscriber_device_status_enum",
        create_type=False,
    )
    subscriber_device_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add Feature Flags & Configurations to `tenants`
    op.add_column("tenants", sa.Column("isp_module_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("bgp_looking_glass_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("sfp_ddm_telemetry_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("ipfix_analytics_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("enforce_maker_checker", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("auto_safemode_enforced", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("ai_mcp_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("nightly_backups_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("outbound_webhooks_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("config_drift_monitoring_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("cis_audit_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("tenants", sa.Column("sdwan_orchestrator_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("capsman_wifi_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("sla_tracker_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("mass_outage_threshold", sa.Integer(), nullable=False, server_default=sa.text("10")))
    op.add_column("tenants", sa.Column("default_locale", sa.String(5), nullable=False, server_default=sa.text("'es'")))

    # 3. Create Table: `bandwidth_profiles`
    op.create_table(
        "bandwidth_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("rate_down_kbps", sa.Integer(), nullable=False),
        sa.Column("rate_up_kbps", sa.Integer(), nullable=False),
        sa.Column("burst_down_kbps", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("burst_up_kbps", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("burst_threshold_down_kbps", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("burst_threshold_up_kbps", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("burst_time_seconds", sa.Integer(), nullable=False, server_default=sa.text("8")),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default=sa.text("8")),
        sa.Column("queue_type", sa.String(64), nullable=False, server_default=sa.text("'pcq-download-default'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_bandwidth_profiles_tenant_name"),
    )
    op.create_index("idx_bandwidth_profiles_tenant", "bandwidth_profiles", ["tenant_id"])

    # Enable & Force Row Level Security on `bandwidth_profiles`
    op.execute("ALTER TABLE bandwidth_profiles ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE bandwidth_profiles FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_bandwidth_profiles ON bandwidth_profiles
        USING (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)

    # 4. Refactor `customer_services` -> `subscriber_devices`
    # Drop personal data columns from `customer_services`
    op.drop_column("customer_services", "customer_name")
    op.drop_column("customer_services", "customer_code")
    op.drop_column("customer_services", "physical_address")

    # Drop `customer_signature_svg` from `field_installation_orders`
    op.drop_column("field_installation_orders", "customer_signature_svg")

    # Rename `onu_serial_number` -> `device_serial`
    op.alter_column("customer_services", "onu_serial_number", new_column_name="device_serial")
    # Rename `pppoe_username` -> `endpoint_identifier`
    op.alter_column("customer_services", "pppoe_username", new_column_name="endpoint_identifier")

    # Add `bandwidth_profile_id` FK
    op.add_column(
        "customer_services",
        sa.Column(
            "bandwidth_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bandwidth_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Rename table to `subscriber_devices`
    op.rename_table("customer_services", "subscriber_devices")

    # Update indexes and constraints for `subscriber_devices`
    op.drop_constraint("uq_customer_services_router_user", "subscriber_devices", type_="unique")
    op.create_unique_constraint("uq_subscriber_devices_router_endpoint", "subscriber_devices", ["router_id", "endpoint_identifier"])

    # Update RLS policy on renamed table
    op.execute("DROP POLICY IF EXISTS tenant_isolation_customer_services ON subscriber_devices;")
    op.execute("""
        CREATE POLICY tenant_isolation_subscriber_devices ON subscriber_devices
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
    # Reverse subscriber_devices back to customer_services
    op.execute("DROP POLICY IF EXISTS tenant_isolation_subscriber_devices ON subscriber_devices;")
    op.drop_constraint("uq_subscriber_devices_router_endpoint", "subscriber_devices", type_="unique")
    op.rename_table("subscriber_devices", "customer_services")
    op.create_unique_constraint("uq_customer_services_router_user", "customer_services", ["router_id", "endpoint_identifier"])

    op.alter_column("customer_services", "endpoint_identifier", new_column_name="pppoe_username")
    op.alter_column("customer_services", "device_serial", new_column_name="onu_serial_number")
    op.drop_column("customer_services", "bandwidth_profile_id")

    op.add_column("customer_services", sa.Column("physical_address", sa.String(255), nullable=True))
    op.add_column("customer_services", sa.Column("customer_code", sa.String(64), nullable=True))
    op.add_column("customer_services", sa.Column("customer_name", sa.String(128), nullable=False, server_default=sa.text("'Default'")))

    op.add_column("field_installation_orders", sa.Column("customer_signature_svg", sa.Text(), nullable=True))

    op.execute("""
        CREATE POLICY tenant_isolation_customer_services ON customer_services
        USING (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)

    op.drop_table("bandwidth_profiles")

    # Drop Feature Flags columns from tenants
    flag_columns = [
        "isp_module_enabled",
        "bgp_looking_glass_enabled",
        "sfp_ddm_telemetry_enabled",
        "ipfix_analytics_enabled",
        "enforce_maker_checker",
        "auto_safemode_enforced",
        "ai_mcp_integration_enabled",
        "nightly_backups_enabled",
        "outbound_webhooks_enabled",
        "config_drift_monitoring_enabled",
        "cis_audit_enabled",
        "sdwan_orchestrator_enabled",
        "capsman_wifi_enabled",
        "sla_tracker_enabled",
        "mass_outage_threshold",
        "default_locale",
    ]
    for col in flag_columns:
        op.drop_column("tenants", col)
