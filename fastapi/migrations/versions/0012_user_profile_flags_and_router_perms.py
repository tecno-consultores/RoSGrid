# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0012_user_profile_flags_and_router_perms

Revision ID: 0012_user_profile_flags_and_router_perms
Revises: 0011_tenant_rogue_dhcp_flag
Create Date: 2026-11-01 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_user_profile_flags_and_router_perms"
down_revision: str | None = "0011_tenant_rogue_dhcp_flag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "feature_flags_override",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "user_router_permissions",
        sa.Column("can_execute_l2_rpc", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "user_router_permissions",
        sa.Column("can_bulk_edit_l2", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "user_router_permissions",
        sa.Column("can_export_l2_rsc", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("user_router_permissions", "can_export_l2_rsc")
    op.drop_column("user_router_permissions", "can_bulk_edit_l2")
    op.drop_column("user_router_permissions", "can_execute_l2_rpc")
    op.drop_column("users", "feature_flags_override")
