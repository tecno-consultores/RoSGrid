# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

engine = create_async_engine(
    settings.ROSGRID_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def set_tenant_context(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def get_tenant_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session
