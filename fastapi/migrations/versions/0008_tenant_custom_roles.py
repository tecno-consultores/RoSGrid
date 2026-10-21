# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0008_tenant_custom_roles

Revision ID: 0008_tenant_custom_roles
Revises: 0007_fleet_automation_l2_syslog
Create Date: 2026-10-21 18:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_tenant_custom_roles"
down_revision: str | None = "0007_fleet_automation_l2_syslog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_custom_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role_name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "role_name", name="uq_tenant_custom_role"),
    )

    op.execute("ALTER TABLE tenant_custom_roles ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tenant_custom_roles FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_custom_roles ON tenant_custom_roles
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    """)

    # Permitir roles de red dinámicos y personalizados (ej. L1) sin restricción al ENUM estático
    op.alter_column(
        "routers",
        "network_role",
        type_=sa.String(64),
        postgresql_using="network_role::text",
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_custom_roles ON tenant_custom_roles;")
    op.drop_table("tenant_custom_roles")
