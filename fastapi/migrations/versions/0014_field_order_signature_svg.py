# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""0014_field_order_signature_svg

Revision ID: 0014_field_order_signature_svg
Revises: 0013_tenant_onboarding_flag
Create Date: 2026-11-07 20:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_field_order_signature_svg"
down_revision: str | None = "0013_tenant_onboarding_flag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Restaura customer_signature_svg en field_installation_orders (eliminada en 0005)
    # usando DDL idempotente para tolerar bases de datos donde ya exista o no exista.
    op.execute(
        sa.text(
            "ALTER TABLE field_installation_orders ADD COLUMN IF NOT EXISTS customer_signature_svg TEXT;"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE field_installation_orders DROP COLUMN IF EXISTS customer_signature_svg;"
        )
    )
