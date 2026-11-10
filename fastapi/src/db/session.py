# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import jwt
from fastapi import Request
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

logger = logging.getLogger(__name__)

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


@event.listens_for(AsyncSession.sync_session_class, "after_begin")
def _reapply_rls_context_after_begin(session: Any, _transaction: Any, connection: Any) -> None:
    info = getattr(session, "info", None)
    if not isinstance(info, dict) or not info.get("rls_initialized"):
        return
    tid_str = str(info.get("tenant_id", ""))
    sa_str = str(info.get("is_superadmin", "false"))
    connection.execute(text("SET LOCAL ROLE rosgrid_app"))
    connection.execute(
        text(
            "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
        ),
        {"tid": tid_str, "sa": sa_str},
    )


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def set_tenant_context(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    await session.execute(text("SET LOCAL ROLE rosgrid_app"))
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})
    info = getattr(session, "info", None)
    if isinstance(info, dict):
        info["tenant_id"] = tid_str
        info["is_superadmin"] = sa_str
        info["rls_initialized"] = True


def _resolve_request_rls_state(request: Request) -> tuple[uuid.UUID | None, bool]:
    tid = getattr(request.state, "tenant_id", None)
    is_sa = bool(getattr(request.state, "is_superadmin_global", False))
    if tid is not None:
        if isinstance(tid, uuid.UUID):
            return tid, is_sa
        try:
            return uuid.UUID(str(tid)), is_sa
        except (ValueError, TypeError):
            return None, is_sa

    token = request.cookies.get("__Host-rg_at") or request.cookies.get("rg_at")
    if not token:
        auth_hdr = request.headers.get("Authorization")
        if auth_hdr and auth_hdr.startswith("Bearer "):
            token = auth_hdr[7:].strip()

    if token:
        try:
            payload = jwt.decode(
                token,
                settings.ROSGRID_JWT_SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_signature": True},
            )
            raw_tid = payload.get("tid")
            role_sa = payload.get("rol") == "SUPERADMIN_GLOBAL"
            if raw_tid:
                parsed_tid = uuid.UUID(str(raw_tid))
                request.state.tenant_id = parsed_tid
                request.state.is_superadmin_global = role_sa
                return parsed_tid, role_sa
        except Exception:
            pass

    return None, is_sa


async def get_tenant_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id, is_superadmin = _resolve_request_rls_state(request)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session
