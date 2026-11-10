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
    "router_tags",
    "router_credentials_vault",
    "maintenance_windows",
    "tenant_custom_roles",
    "approval_requests",
    "router_backups",
    "config_templates",
    "bulk_jobs",
    "bulk_job_items",
    "notification_channels",
    "audit_logs",
    "ipam_vrfs",
    "ipam_prefixes",
    "ipam_ip_addresses",
    "bandwidth_profiles",
    "optical_boxes",
    "subscriber_devices",
    "field_installation_orders",
    "fiber_cut_incidents",
    "golden_config_templates",
    "sdwan_spoke_tunnels",
    "sla_probe_metrics",
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


@pytest.mark.asyncio
async def test_postgres_rls_tenant_isolation_under_rosgrid_app_role() -> None:
    """Verifica aislamiento estricto entre Tenant A y Tenant B bajo SET LOCAL ROLE rosgrid_app."""
    db_url = os.environ.get(
        "ROSGRID_DATABASE_URL",
        "postgresql+asyncpg://rosgrid_user:cambiar_en_entorno_local@rosgrid_db:5432/rosgrid",
    )
    engine = create_async_engine(db_url, echo=False)
    tenant_a = "11111111-1111-1111-1111-111111111111"
    tenant_b = "22222222-2222-2222-2222-222222222222"
    try:
        async with engine.connect() as conn:
            # Contexto Tenant A: consultas que intenten leer filas de Tenant B no devuelven nada
            await conn.execute(text("SET LOCAL ROLE rosgrid_app"))
            await conn.execute(
                text(
                    "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', 'false', true)"
                ),
                {"tid": tenant_a},
            )
            res_a = await conn.execute(
                text("SELECT count(*) FROM routers WHERE tenant_id = :tid_b"),
                {"tid_b": tenant_b},
            )
            assert res_a.scalar() == 0

            # Contexto Tenant B: consultas que intenten leer filas de Tenant A no devuelven nada
            await conn.execute(text("SET LOCAL ROLE rosgrid_app"))
            await conn.execute(
                text(
                    "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', 'false', true)"
                ),
                {"tid": tenant_b},
            )
            res_b = await conn.execute(
                text("SELECT count(*) FROM routers WHERE tenant_id = :tid_a"),
                {"tid_a": tenant_a},
            )
            assert res_b.scalar() == 0
    finally:
        await engine.dispose()
