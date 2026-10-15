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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
mutants_x_set_tenant_context__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_set_tenant_context__mutmut)
async def set_tenant_context(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_orig(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_1(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = True) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_2(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = None
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_3(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if (tenant_id is not None) and False else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_4(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if (tenant_id is not None) or True else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_5(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(None) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_6(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_7(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else "XXXX"
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_8(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = None
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_9(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if (is_superadmin) and False else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_10(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if (is_superadmin) or True else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_11(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "XXtrueXX" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_12(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "TRUE" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_13(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "XXfalseXX"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_14(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "FALSE"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_15(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = None
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_16(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        None
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_17(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "XXSELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)XX"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_18(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "select set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_19(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT SET_CONFIG('APP.CURRENT_TENANT_ID', :TID, TRUE), SET_CONFIG('APP.IS_SUPERADMIN_GLOBAL', :SA, TRUE)"
    )
    await session.execute(stmt, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_20(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(None, {"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_21(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, None)


async def x_set_tenant_context__mutmut_22(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute({"tid": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_23(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, )


async def x_set_tenant_context__mutmut_24(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"XXtidXX": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_25(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"TID": tid_str, "sa": sa_str})


async def x_set_tenant_context__mutmut_26(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "XXsaXX": sa_str})


async def x_set_tenant_context__mutmut_27(session: AsyncSession, tenant_id: uuid.UUID | None, is_superadmin: bool = False) -> None:
    tid_str = str(tenant_id) if tenant_id is not None else ""
    sa_str = "true" if is_superadmin else "false"
    stmt = text(
        "SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.is_superadmin_global', :sa, true)"
    )
    await session.execute(stmt, {"tid": tid_str, "SA": sa_str})

mutants_x_set_tenant_context__mutmut['_mutmut_orig'] = x_set_tenant_context__mutmut_orig # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_1'] = x_set_tenant_context__mutmut_1 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_2'] = x_set_tenant_context__mutmut_2 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_3'] = x_set_tenant_context__mutmut_3 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_4'] = x_set_tenant_context__mutmut_4 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_5'] = x_set_tenant_context__mutmut_5 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_6'] = x_set_tenant_context__mutmut_6 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_7'] = x_set_tenant_context__mutmut_7 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_8'] = x_set_tenant_context__mutmut_8 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_9'] = x_set_tenant_context__mutmut_9 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_10'] = x_set_tenant_context__mutmut_10 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_11'] = x_set_tenant_context__mutmut_11 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_12'] = x_set_tenant_context__mutmut_12 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_13'] = x_set_tenant_context__mutmut_13 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_14'] = x_set_tenant_context__mutmut_14 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_15'] = x_set_tenant_context__mutmut_15 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_16'] = x_set_tenant_context__mutmut_16 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_17'] = x_set_tenant_context__mutmut_17 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_18'] = x_set_tenant_context__mutmut_18 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_19'] = x_set_tenant_context__mutmut_19 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_20'] = x_set_tenant_context__mutmut_20 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_21'] = x_set_tenant_context__mutmut_21 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_22'] = x_set_tenant_context__mutmut_22 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_23'] = x_set_tenant_context__mutmut_23 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_24'] = x_set_tenant_context__mutmut_24 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_25'] = x_set_tenant_context__mutmut_25 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_26'] = x_set_tenant_context__mutmut_26 # type: ignore # mutmut generated
mutants_x_set_tenant_context__mutmut['x_set_tenant_context__mutmut_27'] = x_set_tenant_context__mutmut_27 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_tenant_db_session__mutmut)
async def get_tenant_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_orig(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_1(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = None
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_2(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(None, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_3(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, None, None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_4(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr("tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_5(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_6(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", )
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_7(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "XXtenant_idXX", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_8(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "TENANT_ID", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_9(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = None

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_10(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(None, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_11(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, None, False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_12(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", None)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_13(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr("is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_14(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_15(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", )

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_16(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "XXis_superadmin_globalXX", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_17(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "IS_SUPERADMIN_GLOBAL", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_18(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", True)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_19(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(None, tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_20(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, None, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_21(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, None)
        yield session


async def x_get_tenant_db_session__mutmut_22(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(tenant_id, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_23(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, is_superadmin)
        yield session


async def x_get_tenant_db_session__mutmut_24(request: Request) -> AsyncGenerator[AsyncSession]:
    tenant_id = getattr(request.state, "tenant_id", None)
    is_superadmin = getattr(request.state, "is_superadmin_global", False)

    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id, )
        yield session

mutants_x_get_tenant_db_session__mutmut['_mutmut_orig'] = x_get_tenant_db_session__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_1'] = x_get_tenant_db_session__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_2'] = x_get_tenant_db_session__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_3'] = x_get_tenant_db_session__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_4'] = x_get_tenant_db_session__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_5'] = x_get_tenant_db_session__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_6'] = x_get_tenant_db_session__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_7'] = x_get_tenant_db_session__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_8'] = x_get_tenant_db_session__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_9'] = x_get_tenant_db_session__mutmut_9 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_10'] = x_get_tenant_db_session__mutmut_10 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_11'] = x_get_tenant_db_session__mutmut_11 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_12'] = x_get_tenant_db_session__mutmut_12 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_13'] = x_get_tenant_db_session__mutmut_13 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_14'] = x_get_tenant_db_session__mutmut_14 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_15'] = x_get_tenant_db_session__mutmut_15 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_16'] = x_get_tenant_db_session__mutmut_16 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_17'] = x_get_tenant_db_session__mutmut_17 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_18'] = x_get_tenant_db_session__mutmut_18 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_19'] = x_get_tenant_db_session__mutmut_19 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_20'] = x_get_tenant_db_session__mutmut_20 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_21'] = x_get_tenant_db_session__mutmut_21 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_22'] = x_get_tenant_db_session__mutmut_22 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_23'] = x_get_tenant_db_session__mutmut_23 # type: ignore # mutmut generated
mutants_x_get_tenant_db_session__mutmut['x_get_tenant_db_session__mutmut_24'] = x_get_tenant_db_session__mutmut_24 # type: ignore # mutmut generated
