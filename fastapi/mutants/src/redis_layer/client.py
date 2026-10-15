# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors


import redis.asyncio as aioredis

from src.core.config import settings

_redis_client: aioredis.Redis | None = None


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_get_redis_client__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_redis_client__mutmut)
def get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_orig() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_1() -> aioredis.Redis:
    global _redis_client
    if _redis_client is not None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_2() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = None
    return _redis_client


def x_get_redis_client__mutmut_3() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            None,
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_4() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=None,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_5() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=True,
            socket_timeout=None,
        )
    return _redis_client


def x_get_redis_client__mutmut_6() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_7() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_8() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=True,
            )
    return _redis_client


def x_get_redis_client__mutmut_9() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=False,
            socket_timeout=5.0,
        )
    return _redis_client


def x_get_redis_client__mutmut_10() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.ROSGRID_REDIS_URL,
            decode_responses=True,
            socket_timeout=6.0,
        )
    return _redis_client

mutants_x_get_redis_client__mutmut['_mutmut_orig'] = x_get_redis_client__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_1'] = x_get_redis_client__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_2'] = x_get_redis_client__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_3'] = x_get_redis_client__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_4'] = x_get_redis_client__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_5'] = x_get_redis_client__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_6'] = x_get_redis_client__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_7'] = x_get_redis_client__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_8'] = x_get_redis_client__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_9'] = x_get_redis_client__mutmut_9 # type: ignore # mutmut generated
mutants_x_get_redis_client__mutmut['x_get_redis_client__mutmut_10'] = x_get_redis_client__mutmut_10 # type: ignore # mutmut generated
mutants_x_close_redis_client__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_close_redis_client__mutmut)
async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def x_close_redis_client__mutmut_orig() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def x_close_redis_client__mutmut_1() -> None:
    global _redis_client
    if _redis_client is None:
        await _redis_client.aclose()
        _redis_client = None


async def x_close_redis_client__mutmut_2() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = ""

mutants_x_close_redis_client__mutmut['_mutmut_orig'] = x_close_redis_client__mutmut_orig # type: ignore # mutmut generated
mutants_x_close_redis_client__mutmut['x_close_redis_client__mutmut_1'] = x_close_redis_client__mutmut_1 # type: ignore # mutmut generated
mutants_x_close_redis_client__mutmut['x_close_redis_client__mutmut_2'] = x_close_redis_client__mutmut_2 # type: ignore # mutmut generated
