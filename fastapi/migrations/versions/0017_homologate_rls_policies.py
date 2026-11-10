# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""0017_homologate_rls_policies

Revision ID: 0017_homologate_rls_policies
Revises: 0016_rls_worm_seq_and_fk_idx
Create Date: 2026-11-09 22:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_homologate_rls_policies"
down_revision: str | None = "0016_rls_worm_seq_and_fk_idx"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_POLICY_MAP: tuple[tuple[str, str], ...] = (
    ("users", "tenant_isolation_users"),
    ("user_router_permissions", "tenant_isolation_urp"),
    ("routers", "tenant_isolation_routers"),
    ("router_tags", "tenant_isolation_router_tags"),
    ("router_credentials_vault", "tenant_isolation_vault"),
    ("maintenance_windows", "tenant_isolation_maint"),
    ("tenant_custom_roles", "tenant_isolation_custom_roles"),
    ("approval_requests", "tenant_isolation_approval_requests"),
    ("router_backups", "tenant_isolation_router_backups"),
    ("config_templates", "tenant_isolation_config_templates"),
    ("bulk_jobs", "tenant_isolation_bulk_jobs"),
    ("bulk_job_items", "tenant_isolation_bulk_job_items"),
    ("notification_channels", "tenant_isolation_notification_channels"),
    ("audit_logs", "tenant_isolation_audit"),
    ("ipam_vrfs", "tenant_isolation_ipam_vrfs"),
    ("ipam_prefixes", "tenant_isolation_ipam_prefixes"),
    ("ipam_ip_addresses", "tenant_isolation_ipam_addresses"),
    ("bandwidth_profiles", "tenant_isolation_bandwidth_profiles"),
    ("optical_boxes", "tenant_isolation_optical_boxes"),
    ("subscriber_devices", "tenant_isolation_subscriber_devices"),
    ("field_installation_orders", "tenant_isolation_field_orders"),
    ("fiber_cut_incidents", "tenant_isolation_fiber_cuts"),
    ("golden_config_templates", "tenant_isolation_golden_config_templates"),
    ("sdwan_spoke_tunnels", "tenant_isolation_sdwan_spoke_tunnels"),
    ("sla_probe_metrics", "tenant_isolation_sla_probe_metrics"),
)


def upgrade() -> None:
    """Homologa las 25 políticas RLS multi-tenant reales con cláusula app.is_superadmin_global."""
    for table_name, policy_name in _TENANT_POLICY_MAP:
        op.execute(sa.text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"))
        op.execute(sa.text(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;"))
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
                    ELSE
                        CREATE POLICY {policy_name} ON {table_name}
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
    """No-op para preservar aislamiento multi-tenant y acceso global de SuperAdmin."""
    pass
