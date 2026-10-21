# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0009_audit_logs_worm_decouple_fk

Revision ID: 0009_audit_logs_worm_decouple_fk
Revises: 0008_tenant_custom_roles
Create Date: 2026-10-21 19:15:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_audit_logs_worm_decouple_fk"
down_revision: str | None = "0008_tenant_custom_roles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Decouple foreign keys from immutable WORM table audit_logs.
    # When a router or user is deleted, ON DELETE SET NULL previously triggered an UPDATE statement,
    # which contradicted and was rejected by trg_immutable_audit_logs (PL/pgSQL exception 42501).
    # Furthermore, in forensic WORM ledgers, the entity UUID must be permanently retained without mutation.
    op.drop_constraint("audit_logs_router_id_fkey", "audit_logs", type_="foreignkey")
    op.drop_constraint("audit_logs_actor_user_id_fkey", "audit_logs", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "audit_logs_router_id_fkey",
        "audit_logs",
        "routers",
        ["router_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "audit_logs_actor_user_id_fkey",
        "audit_logs",
        "users",
        ["actor_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
