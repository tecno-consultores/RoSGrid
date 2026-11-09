# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""0015_tenant_hq_coordinates

Revision ID: 0015_tenant_hq_coordinates
Revises: 0014_field_order_signature_svg
Create Date: 2026-11-08 13:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_tenant_hq_coordinates"
down_revision: str | None = "0014_field_order_signature_svg"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Coordenadas GPS Sede Principal (Spec 104) con DDL idempotente
    op.execute(
        sa.text(
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS hq_latitude NUMERIC(9, 6) DEFAULT 10.480600;"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS hq_longitude NUMERIC(9, 6) DEFAULT -66.903600;"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE tenants DROP COLUMN IF EXISTS hq_longitude;"))
    op.execute(sa.text("ALTER TABLE tenants DROP COLUMN IF EXISTS hq_latitude;"))
