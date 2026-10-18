# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0004_ipam_and_field_ops

Revision ID: 0004_ipam_and_field_ops
Revises: 0003_operations
Create Date: 2026-10-18 14:58:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_ipam_and_field_ops"
down_revision: str | None = "0003_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. ENUMs
    ip_family_enum = postgresql.ENUM("IPv4", "IPv6", name="ip_family_enum", create_type=False)
    ip_prefix_role_enum = postgresql.ENUM(
        "CGNAT",
        "PUBLIC_DYNAMIC",
        "PUBLIC_STATIC",
        "INFRA_P2P",
        "LOOPBACK",
        "CUSTOMER_RESIDENTIAL",
        "CUSTOMER_CORPORATE",
        "MGMT",
        name="ip_prefix_role_enum",
        create_type=False,
    )
    ip_prefix_status_enum = postgresql.ENUM("ACTIVE", "RESERVED", "DEPRECATED", name="ip_prefix_status_enum", create_type=False)
    ip_address_status_enum = postgresql.ENUM(
        "ALLOCATED", "RESERVED", "SOFT_LOCKED", "DHCP_STATIC", "DHCP_DYNAMIC", "QUARANTINE", "DEPRECATED",
        name="ip_address_status_enum",
        create_type=False,
    )
    customer_service_type_enum = postgresql.ENUM("PPPOE", "DHCP", "STATIC", name="customer_service_type_enum", create_type=False)
    auth_backend_enum = postgresql.ENUM("LOCAL_SECRET", "RADIUS", name="auth_backend_enum", create_type=False)
    onu_mode_enum = postgresql.ENUM("ROUTER", "BRIDGE", "UNKNOWN", name="onu_mode_enum", create_type=False)
    customer_service_status_enum = postgresql.ENUM(
        "ACTIVE", "PENDING_INSTALL", "SUSPENDED", "TERMINATED", name="customer_service_status_enum", create_type=False
    )
    field_order_status_enum = postgresql.ENUM(
        "ASSIGNED", "IN_PROGRESS", "CERTIFIED", "FAILED", "CANCELLED", name="field_order_status_enum", create_type=False
    )
    fiber_cut_status_enum = postgresql.ENUM("DETECTED", "INVESTIGATING", "RESOLVED", name="fiber_cut_status_enum", create_type=False)

    ip_family_enum.create(op.get_bind(), checkfirst=True)
    ip_prefix_role_enum.create(op.get_bind(), checkfirst=True)
    ip_prefix_status_enum.create(op.get_bind(), checkfirst=True)
    ip_address_status_enum.create(op.get_bind(), checkfirst=True)
    customer_service_type_enum.create(op.get_bind(), checkfirst=True)
    auth_backend_enum.create(op.get_bind(), checkfirst=True)
    onu_mode_enum.create(op.get_bind(), checkfirst=True)
    customer_service_status_enum.create(op.get_bind(), checkfirst=True)
    field_order_status_enum.create(op.get_bind(), checkfirst=True)
    fiber_cut_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Table: ipam_vrfs
    op.create_table(
        "ipam_vrfs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("route_distinguisher", sa.String(32), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ipam_vrfs_tenant_name"),
    )

    # 3. Table: ipam_prefixes
    op.create_table(
        "ipam_prefixes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vrf_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ipam_vrfs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ipam_prefixes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("prefix", postgresql.CIDR(), nullable=False),
        sa.Column("ip_family", ip_family_enum, nullable=False),
        sa.Column("role", ip_prefix_role_enum, nullable=False, server_default=sa.text("'CUSTOMER_RESIDENTIAL'")),
        sa.Column("status", ip_prefix_status_enum, nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("is_pool", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_child_prefix_len", sa.SmallInteger(), nullable=True),
        sa.Column("utilization_pct", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "vrf_id", "prefix", name="uq_ipam_prefix_tenant_vrf"),
    )
    op.create_index("idx_ipam_prefixes_cidr_gist", "ipam_prefixes", ["prefix"], postgresql_using="gist", postgresql_ops={"prefix": "inet_ops"})
    op.create_index("idx_ipam_prefixes_tenant_vrf", "ipam_prefixes", ["tenant_id", "vrf_id", "ip_family"])

    # 4. Table: ipam_ip_addresses
    op.create_table(
        "ipam_ip_addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prefix_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ipam_prefixes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("address", postgresql.INET(), nullable=False),
        sa.Column("ip_family", ip_family_enum, nullable=False),
        sa.Column("status", ip_address_status_enum, nullable=False, server_default=sa.text("'ALLOCATED'")),
        sa.Column("router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interface_name", sa.String(64), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        sa.Column("dns_ptr", sa.String(255), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("soft_lock_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("prefix_id", "address", name="uq_ipam_addresses_prefix_addr"),
    )
    op.create_index("idx_ipam_ip_address_inet_gist", "ipam_ip_addresses", ["address"], postgresql_using="gist", postgresql_ops={"address": "inet_ops"})
    op.create_index("idx_ipam_ip_addresses_mac", "ipam_ip_addresses", ["tenant_id", "mac_address"])

    # 5. Table: customer_services
    op.create_table(
        "customer_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_name", sa.String(128), nullable=False),
        sa.Column("customer_code", sa.String(64), nullable=True),
        sa.Column("service_type", customer_service_type_enum, nullable=False, server_default=sa.text("'PPPOE'")),
        sa.Column("auth_backend", auth_backend_enum, nullable=False, server_default=sa.text("'LOCAL_SECRET'")),
        sa.Column("pppoe_username", sa.String(64), nullable=True),
        sa.Column("pppoe_password_vault_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ipv4_address_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ipam_ip_addresses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ipv6_delegated_prefix", postgresql.CIDR(), nullable=True),
        sa.Column("onu_mode", onu_mode_enum, nullable=False, server_default=sa.text("'ROUTER'")),
        sa.Column("onu_mac_address", sa.String(17), nullable=True),
        sa.Column("onu_serial_number", sa.String(64), nullable=True),
        sa.Column("cpe_wifi_mac_address", sa.String(17), nullable=True),
        sa.Column("pon_port", sa.String(64), nullable=True),
        sa.Column("optical_box", sa.String(64), nullable=True),
        sa.Column("last_reachability_status", sa.String(20), nullable=False, server_default=sa.text("'ONLINE'")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", customer_service_status_enum, nullable=False, server_default=sa.text("'PENDING_INSTALL'")),
        sa.Column("physical_address", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("router_id", "pppoe_username", name="uq_customer_services_router_user"),
    )
    op.create_index("idx_customer_services_tenant_status", "customer_services", ["tenant_id", "status"])
    op.create_index("idx_customer_services_onu_sn", "customer_services", ["tenant_id", "onu_serial_number"])
    op.create_index("idx_customer_services_pon_port", "customer_services", ["tenant_id", "router_id", "pon_port"])

    # 6. Table: field_installation_orders
    op.create_table(
        "field_installation_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_tech_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", field_order_status_enum, nullable=False, server_default=sa.text("'ASSIGNED'")),
        sa.Column("onu_scanned_serial", sa.String(64), nullable=True),
        sa.Column("onu_scanned_mac", sa.String(17), nullable=True),
        sa.Column("detected_mode", sa.String(20), nullable=True),
        sa.Column("ping_avg_ms", sa.Numeric(6, 2), nullable=True),
        sa.Column("ping_loss_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("traffic_rx_kbps", sa.Numeric(10, 2), nullable=True),
        sa.Column("traffic_tx_kbps", sa.Numeric(10, 2), nullable=True),
        sa.Column("tech_latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("tech_longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("customer_signature_svg", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("certified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_field_orders_tech", "field_installation_orders", ["assigned_tech_id", "status"])

    # 7. Table: fiber_cut_incidents
    op.create_table(
        "fiber_cut_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pon_port", sa.String(64), nullable=False),
        sa.Column("optical_box", sa.String(64), nullable=True),
        sa.Column("affected_onus_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", fiber_cut_status_enum, nullable=False, server_default=sa.text("'DETECTED'")),
        sa.Column("incident_summary", sa.String(255), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_fiber_cut_incidents_tenant", "fiber_cut_incidents", ["tenant_id", "status"])

    # 8. RLS Policies (Row-Level Security)
    tables = [
        ("ipam_vrfs", "tenant_isolation_ipam_vrfs"),
        ("ipam_prefixes", "tenant_isolation_ipam_prefixes"),
        ("ipam_ip_addresses", "tenant_isolation_ipam_addresses"),
        ("customer_services", "tenant_isolation_customer_services"),
        ("field_installation_orders", "tenant_isolation_field_orders"),
        ("fiber_cut_incidents", "tenant_isolation_fiber_cuts"),
    ]

    for table_name, policy_name in tables:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {policy_name} ON {table_name}
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
    tables = [
        ("fiber_cut_incidents", "tenant_isolation_fiber_cuts"),
        ("field_installation_orders", "tenant_isolation_field_orders"),
        ("customer_services", "tenant_isolation_customer_services"),
        ("ipam_ip_addresses", "tenant_isolation_ipam_addresses"),
        ("ipam_prefixes", "tenant_isolation_ipam_prefixes"),
        ("ipam_vrfs", "tenant_isolation_ipam_vrfs"),
    ]

    for table_name, policy_name in tables:
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table_name};")

    op.drop_table("fiber_cut_incidents")
    op.drop_table("field_installation_orders")
    op.drop_table("customer_services")
    op.drop_table("ipam_ip_addresses")
    op.drop_table("ipam_prefixes")
    op.drop_table("ipam_vrfs")

    enums = [
        "fiber_cut_status_enum",
        "field_order_status_enum",
        "customer_service_status_enum",
        "onu_mode_enum",
        "auth_backend_enum",
        "customer_service_type_enum",
        "ip_address_status_enum",
        "ip_prefix_status_enum",
        "ip_prefix_role_enum",
        "ip_family_enum",
    ]
    for e in enums:
        op.execute(f"DROP TYPE IF EXISTS {e};")
