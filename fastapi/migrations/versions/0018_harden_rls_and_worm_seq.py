# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""0018_harden_rls_and_worm_seq

Revision ID: 0018_harden_rls_and_worm_seq
Revises: 0017_homologate_rls_policies
Create Date: 2026-11-10 14:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_harden_rls_and_worm_seq"
down_revision: str | None = "0017_homologate_rls_policies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Blindaje WORM: Revocar UPDATE y DELETE en audit_logs para rosgrid_app
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rosgrid_app') THEN
                    REVOKE UPDATE, DELETE ON TABLE audit_logs FROM rosgrid_app;
                    REVOKE INSERT, UPDATE, DELETE ON TABLE alembic_version FROM rosgrid_app;
                END IF;
            END
            $$;
            """
        )
    )

    # 2. Privilegios por defecto para tablas y secuencias futuras
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rosgrid_app') THEN
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rosgrid_app;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO rosgrid_app;
                END IF;
            END
            $$;
            """
        )
    )

    # 3. Eliminar función helper obsoleta SECURITY DEFINER
    op.execute(sa.text("DROP FUNCTION IF EXISTS fn_resolve_tenant_by_slug(VARCHAR);"))

    # 4. Reasignar secuencia WORM monotónica a filas existentes con seq_num = 0
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs'
                ) AND EXISTS (
                    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_immutable_audit_logs'
                ) THEN
                    ALTER TABLE audit_logs DISABLE TRIGGER trg_immutable_audit_logs;
                    UPDATE audit_logs SET seq_num = nextval('audit_logs_seq_num_seq') WHERE seq_num = 0;
                    ALTER TABLE audit_logs ENABLE TRIGGER trg_immutable_audit_logs;
                END IF;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rosgrid_app') THEN
                    GRANT UPDATE, DELETE ON TABLE audit_logs TO rosgrid_app;
                    GRANT INSERT, UPDATE, DELETE ON TABLE alembic_version TO rosgrid_app;
                END IF;
            END
            $$;
            """
        )
    )
