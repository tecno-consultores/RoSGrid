# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0007_fleet_automation_l2_syslog_flags

Revision ID: 0007_fleet_automation_l2_syslog
Revises: 0006_compliance_sdwan_sla
Create Date: 2026-10-20 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_fleet_automation_l2_syslog"
down_revision: str | None = "0006_compliance_sdwan_sla"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Agrega 4 columnas de Feature Flags para Hito 23 (Spec 35) a la tabla tenants
    op.add_column(
        "tenants",
        sa.Column("l2_topology_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "tenants",
        sa.Column("syslog_collector_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "tenants",
        sa.Column("cve_scanner_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "tenants",
        sa.Column("prometheus_fleet_exporter_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("tenants", "prometheus_fleet_exporter_enabled")
    op.drop_column("tenants", "cve_scanner_enabled")
    op.drop_column("tenants", "syslog_collector_enabled")
    op.drop_column("tenants", "l2_topology_enabled")
