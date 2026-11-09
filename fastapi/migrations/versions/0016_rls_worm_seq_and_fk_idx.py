# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""0016_rls_worm_seq_and_fk_idx

Revision ID: 0016_rls_worm_seq_and_fk_idx
Revises: 0015_tenant_hq_coordinates
Create Date: 2026-11-09 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_rls_worm_seq_and_fk_idx"
down_revision: str | None = "0015_tenant_hq_coordinates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_TABLES_WITH_RLS = (
    "routers",
    "router_credentials_vault",
    "tags",
    "user_router_permissions",
    "approval_requests",
    "bulk_jobs",
    "router_backups",
    "maintenance_windows",
    "notification_channels",
    "audit_logs",
    "ipam_vlans",
    "ipam_vrfs",
    "ipam_prefixes",
    "ipam_ip_addresses",
    "bandwidth_profiles",
    "nap_splitter_boxes",
    "subscriber_devices",
    "customer_services",
    "field_installation_orders",
    "golden_config_templates",
    "sdwan_spoke_tunnels",
    "sla_probe_metrics",
)


def upgrade() -> None:
    # 1. Secuencia monotónica WORM en audit_logs (pausando temporalmente el trigger de inmutabilidad)
    op.execute(sa.text("ALTER TABLE audit_logs DISABLE TRIGGER trg_immutable_audit_logs;"))
    op.execute(sa.text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS seq_num BIGSERIAL NOT NULL;"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_audit_tenant_seq ON audit_logs (tenant_id, seq_num DESC);"))
    op.execute(sa.text("ALTER TABLE audit_logs ENABLE TRIGGER trg_immutable_audit_logs;"))

    # 2. Índices faltantes en claves foráneas de alta concurrencia
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_sub_devices_tenant_router ON subscriber_devices (tenant_id, router_id);"
        )
    )
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_ipam_ip_prefix_id ON ipam_ip_addresses (prefix_id);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_ipam_prefixes_parent_id ON ipam_prefixes (parent_id);"))
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_field_orders_cs_id ON field_installation_orders (customer_service_id);"
        )
    )
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_bulk_jobs_approval_id ON bulk_jobs (approval_request_id);"))

    # 3. Rol de aplicación sin privilegios de superusuario (NOSUPERUSER NOBYPASSRLS) y helper SECURITY DEFINER
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rosgrid_app') THEN
                    CREATE ROLE rosgrid_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
                END IF;
            END
            $$;
            GRANT USAGE ON SCHEMA public TO rosgrid_app;
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rosgrid_app;
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rosgrid_app;
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION fn_resolve_tenant_by_slug(p_slug VARCHAR)
            RETURNS TABLE(id UUID, slug VARCHAR, status tenant_status_enum)
            LANGUAGE sql
            SECURITY DEFINER
            SET search_path = public
            AS $$
                SELECT t.id, t.slug, t.status FROM tenants t WHERE t.slug = p_slug LIMIT 1;
            $$;
            """
        )
    )

    # 4. Homologar políticas RLS con cláusula app.is_superadmin_global en todas las tablas multi-tenant
    for table_name in _TENANT_TABLES_WITH_RLS:
        policy_name = f"tenant_isolation_{table_name}"
        op.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_policies
                        WHERE schemaname = 'public' AND tablename = '{table_name}' AND policyname = '{policy_name}'
                    ) THEN
                        ALTER POLICY {policy_name} ON {table_name}
                        USING (
                            current_setting('app.is_superadmin_global', true) = 'true'
                            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
                        )
                        WITH CHECK (
                            current_setting('app.is_superadmin_global', true) = 'true'
                            OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
                        );
                    END IF;
                END
                $$;
                """
            )
        )


def downgrade() -> None:
    op.execute(sa.text("DROP FUNCTION IF EXISTS fn_resolve_tenant_by_slug(VARCHAR);"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_bulk_jobs_approval_id;"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_field_orders_cs_id;"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_ipam_prefixes_parent_id;"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_ipam_ip_prefix_id;"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_sub_devices_tenant_router;"))
    op.execute(sa.text("ALTER TABLE audit_logs DISABLE TRIGGER trg_immutable_audit_logs;"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_audit_tenant_seq;"))
    op.execute(sa.text("ALTER TABLE audit_logs DROP COLUMN IF EXISTS seq_num;"))
    op.execute(sa.text("ALTER TABLE audit_logs ENABLE TRIGGER trg_immutable_audit_logs;"))
