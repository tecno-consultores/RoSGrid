# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""0013_tenant_onboarding_flag

Revision ID: 0013_tenant_onboarding_flag
Revises: 0012_user_profile_flags_perms
Create Date: 2026-11-02 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_tenant_onboarding_flag"
down_revision: str | None = "0012_user_profile_flags_perms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # Backfill automático: marcar onboarding_completed = TRUE para todo tenant existente
    # que ya haya configurado sus Feature Flags o que ya tenga routers registrados.
    op.execute(
        sa.text(
            """
            UPDATE tenants t
            SET onboarding_completed = TRUE
            WHERE EXISTS (
                SELECT 1 FROM audit_logs a
                WHERE a.tenant_id = t.id AND a.event_action = 'TENANT_FEATURE_FLAGS_UPDATED'
            ) OR EXISTS (
                SELECT 1 FROM routers r
                WHERE r.tenant_id = t.id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("tenants", "onboarding_completed")
