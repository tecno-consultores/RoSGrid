# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Suite de Integración Real contra PostgreSQL 17 y Alembic (RLS Multi-Tenant y Paridad de Esquema).

Se ejecuta bajo el marcador `@pytest.mark.integration` contra el contenedor `rosgrid-db`
definido en `fastapi/docker-compose.qa.yml` (`make qa-integration`).
"""

import os
import subprocess

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.models import Base

pytestmark = pytest.mark.integration

EXPECTED_RLS_TABLES: tuple[str, ...] = (
    "users",
    "user_router_permissions",
    "routers",
    "router_credentials_vault",
    "maintenance_windows",
    "router_backups",
    "approval_requests",
    "config_templates",
    "bulk_jobs",
    "bulk_job_items",
    "notification_channels",
    "immutable_audit_logs",
    "ipam_pools",
    "ipam_reservations",
    "bandwidth_profiles",
    "subscriber_devices",
    "router_config_snapshots",
    "router_compliance_reports",
    "vpn_tunnels",
    "bgp_sessions",
    "netflow_top_talkers",
    "tenant_sla_targets",
    "router_sla_daily_rollups",
    "network_incident_events",
    "tenant_custom_roles",
)


@pytest.mark.asyncio
async def test_postgres_alembic_head_and_rls_policies_enforced() -> None:
    """Verifica que `alembic upgrade head` aplique limpiamente y las 25 tablas tengan RLS FORCE activo."""
    db_url = os.environ.get(
        "ROSGRID_DATABASE_URL",
        "postgresql+asyncpg://rosgrid_user:cambiar_en_entorno_local@rosgrid_db:5432/rosgrid",
    )
    res = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"Fallo en alembic upgrade head: {res.stderr}"

    engine = create_async_engine(db_url, echo=False)
    try:
        async with engine.connect() as conn:
            # 1. Verificar que todas las tablas del ORM existen físicamente en PostgreSQL
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT tablename, rowsecurity, forcerowsecurity FROM pg_tables WHERE schemaname = 'public'"
                        )
                    )
                )
                .mappings()
                .all()
            )
            pg_table_map = {r["tablename"]: r for r in rows}

            for orm_table in Base.metadata.tables:
                assert orm_table in pg_table_map, f"Tabla ORM '{orm_table}' no existe en PostgreSQL tras migración"

            # 2. Verificar que las 25 tablas multi-tenant tienen ENABLE y FORCE ROW LEVEL SECURITY
            for rls_table in EXPECTED_RLS_TABLES:
                assert rls_table in pg_table_map, f"Tabla RLS '{rls_table}' ausente en PostgreSQL"
                assert pg_table_map[rls_table]["rowsecurity"] is True, f"RLS inactivo en {rls_table}"
                assert pg_table_map[rls_table]["forcerowsecurity"] is True, f"FORCE RLS inactivo en {rls_table}"

            # 3. Verificar que todas las políticas RLS admiten bypass explícito de superadmin_global
            pol_rows = (
                (
                    await conn.execute(
                        text("SELECT tablename, policyname, qual FROM pg_policies WHERE schemaname = 'public'")
                    )
                )
                .mappings()
                .all()
            )
            pol_by_table = {r["tablename"]: r for r in pol_rows}

            for rls_table in EXPECTED_RLS_TABLES:
                assert rls_table in pol_by_table, f"Sin política RLS registrada en pg_policies para {rls_table}"
                qual_expr = str(pol_by_table[rls_table]["qual"] or "")
                assert "app.current_tenant_id" in qual_expr, f"Política en {rls_table} no filtra por tenant_id"
                assert "app.is_superadmin_global" in qual_expr, (
                    f"Política en {rls_table} no incluye cláusula app.is_superadmin_global"
                )
    finally:
        await engine.dispose()
