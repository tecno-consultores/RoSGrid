# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0010_optical_boxes_ftth

Revision ID: 0010_optical_boxes_ftth
Revises: 0009_audit_logs_worm_decouple_fk
Create Date: 2026-10-24 15:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_optical_boxes_ftth"
down_revision: str | None = "0009_audit_logs_worm_decouple_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tabla: optical_boxes (Infraestructura Pasiva / Cajas NAP / ODB)
    op.create_table(
        "optical_boxes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("router_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("box_code", sa.String(64), nullable=False),
        sa.Column("brand", sa.String(64), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("capacity_ports", sa.Integer(), nullable=False, server_default=sa.text("16")),
        sa.Column("splitter_ratio", sa.String(20), nullable=False, server_default=sa.text("'1:16'")),
        sa.Column("installation_type", sa.String(32), nullable=False, server_default=sa.text("'POLE'")),
        sa.Column("physical_location", sa.String(255), nullable=True),
        sa.Column("input_power_dbm", sa.Numeric(5, 2), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "box_code", name="uq_optical_boxes_tenant_code"),
    )
    op.create_index("idx_optical_boxes_tenant_status", "optical_boxes", ["tenant_id", "status"])
    op.create_index("idx_optical_boxes_router", "optical_boxes", ["tenant_id", "router_id"])

    # Políticas de RLS en optical_boxes
    op.execute("ALTER TABLE optical_boxes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE optical_boxes FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_optical_boxes ON optical_boxes
        USING (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            current_setting('app.is_superadmin_global', true) = 'true'
            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """)

    # 2. Extensión de subscriber_devices para Cajas NAP y coordenadas personalizadas
    op.add_column(
        "subscriber_devices",
        sa.Column(
            "optical_box_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("optical_boxes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("subscriber_devices", sa.Column("optical_box_port", sa.SmallInteger(), nullable=True))
    op.add_column("subscriber_devices", sa.Column("rx_optical_power_dbm", sa.Numeric(5, 2), nullable=True))
    op.add_column("subscriber_devices", sa.Column("drop_cable_meters", sa.Integer(), nullable=True))
    op.add_column(
        "subscriber_devices",
        sa.Column("is_custom_coordinates", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("idx_subscriber_devices_optical_box", "subscriber_devices", ["tenant_id", "optical_box_id"])


def downgrade() -> None:
    op.drop_index("idx_subscriber_devices_optical_box", "subscriber_devices")
    op.drop_column("subscriber_devices", "is_custom_coordinates")
    op.drop_column("subscriber_devices", "drop_cable_meters")
    op.drop_column("subscriber_devices", "rx_optical_power_dbm")
    op.drop_column("subscriber_devices", "optical_box_port")
    op.drop_column("subscriber_devices", "optical_box_id")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_optical_boxes ON optical_boxes;")
    op.drop_index("idx_optical_boxes_router", "optical_boxes")
    op.drop_index("idx_optical_boxes_tenant_status", "optical_boxes")
    op.drop_table("optical_boxes")
