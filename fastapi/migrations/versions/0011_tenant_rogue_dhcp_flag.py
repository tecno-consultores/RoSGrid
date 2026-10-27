# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0011_tenant_rogue_dhcp_flag

Revision ID: 0011_tenant_rogue_dhcp_flag
Revises: 0010_optical_boxes_ftth
Create Date: 2026-10-27 18:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_tenant_rogue_dhcp_flag"
down_revision: str | None = "0010_optical_boxes_ftth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Agrega columna rogue_dhcp_enabled a la tabla tenants
    op.add_column(
        "tenants",
        sa.Column("rogue_dhcp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("tenants", "rogue_dhcp_enabled")
