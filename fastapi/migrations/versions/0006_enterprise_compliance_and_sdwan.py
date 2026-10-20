# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0006_enterprise_compliance_and_sdwan

Revision ID: 0006_compliance_sdwan_sla
Revises: 0005_feature_flags_qos
Create Date: 2026-10-19 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_compliance_sdwan_sla"
down_revision: str | None = "0005_feature_flags_qos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Table: golden_config_templates
    op.create_table(
        "golden_config_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("network_role", sa.String(64), nullable=False, server_default=sa.text("'BRANCH'")),
        sa.Column("baseline_rsc_content", sa.Text(), nullable=False),
        sa.Column("enforce_strict_firewall", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("enforce_ntp_dns", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_golden_template_tenant_name"),
    )
    op.create_index("ix_golden_config_templates_tenant_id", "golden_config_templates", ["tenant_id"])

    # 2. Create Table: sdwan_spoke_tunnels
    op.create_table(
        "sdwan_spoke_tunnels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hub_router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spoke_router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spoke_name", sa.String(120), nullable=False),
        sa.Column("interface_name", sa.String(64), nullable=False, server_default=sa.text("'wg-sdwan0'")),
        sa.Column("allocated_subnet", sa.String(64), nullable=False),
        sa.Column("hub_endpoint", sa.String(128), nullable=False),
        sa.Column("spoke_public_key", sa.String(128), nullable=False),
        sa.Column("routing_protocol", sa.String(32), nullable=False, server_default=sa.text("'OSPF'")),
        sa.Column("multi_wan_failover_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "spoke_router_id", name="uq_sdwan_spoke_router"),
    )
    op.create_index("ix_sdwan_spoke_tunnels_tenant_id", "sdwan_spoke_tunnels", ["tenant_id"])

    # 3. Create Table: sla_probe_metrics
    op.create_table(
        "sla_probe_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_host", sa.String(128), nullable=False),
        sa.Column("target_name", sa.String(120), nullable=False, server_default=sa.text("'Carrier Gateway'")),
        sa.Column("uptime_percent", sa.Float(), nullable=False, server_default=sa.text("100.0")),
        sa.Column("avg_latency_ms", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("p95_latency_ms", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("p99_latency_ms", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("jitter_ms", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("packet_loss_pct", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("sla_threshold_ms", sa.Float(), nullable=False, server_default=sa.text("50.0")),
        sa.Column("compliance_status", sa.String(32), nullable=False, server_default=sa.text("'COMPLIANT'")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sla_probe_metrics_tenant_id", "sla_probe_metrics", ["tenant_id"])
    op.create_index("ix_sla_probe_metrics_router_id", "sla_probe_metrics", ["router_id"])

    # 4. Enable Row Level Security (RLS) on new tables
    tables = [
        "golden_config_templates",
        "sdwan_spoke_tunnels",
        "sla_probe_metrics",
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            FOR ALL
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """)


def downgrade() -> None:
    tables = [
        "sla_probe_metrics",
        "sdwan_spoke_tunnels",
        "golden_config_templates",
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.drop_table(table)
