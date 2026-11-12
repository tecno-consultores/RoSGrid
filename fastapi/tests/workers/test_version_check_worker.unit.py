# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias para el Worker de Comprobación Pasiva de Versiones (Hito 30.42)."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.api.v1.system import read_version_check_status, trigger_version_check_refresh
from src.core.config import settings
from src.schemas.diagnostics_siem import VersionCheckStatusResponse
from src.workers.version_check_worker import (
    ALLOWED_GITHUB_RELEASE_PREFIX,
    DEFAULT_RELEASES_PAGE,
    _decode_redis_val,
    _sanitize_release_url,
    check_github_release_once,
    get_version_check_status,
    is_newer_semver,
    parse_semver_tuple,
    version_check_worker_loop,
)


def test_parse_semver_tuple_valid_and_invalid() -> None:
    """Verifica el parser estricto de tuplas semver."""
    assert parse_semver_tuple("1.2.0") == (1, 2, 0)
    assert parse_semver_tuple("v1.3.5") == (1, 3, 5)
    assert parse_semver_tuple("V2.0.1") == (2, 0, 1)

    # Pre-releases y sufijos descartados
    assert parse_semver_tuple("1.3.0-rc.1") is None
    assert parse_semver_tuple("1.3.0-beta") is None
    assert parse_semver_tuple("1.3.0+build99") is None

    # Formatos malformados o vacíos
    assert parse_semver_tuple(None) is None
    assert parse_semver_tuple("") is None
    assert parse_semver_tuple("1.2") is None
    assert parse_semver_tuple("1.2.x") is None
    assert parse_semver_tuple("abc") is None


def test_is_newer_semver_comparisons() -> None:
    """Verifica las comparaciones de versiones semver."""
    assert is_newer_semver("1.3.0", "1.2.0") is True
    assert is_newer_semver("v1.2.1", "1.2.0") is True
    assert is_newer_semver("2.0.0", "1.99.99") is True

    # Versiones iguales o inferiores
    assert is_newer_semver("1.2.0", "1.2.0") is False
    assert is_newer_semver("1.1.9", "1.2.0") is False
    assert is_newer_semver("1.2.0", "1.2.1") is False

    # Pre-releases o nulos nunca se consideran newer
    assert is_newer_semver("1.3.0-rc1", "1.2.0") is False
    assert is_newer_semver(None, "1.2.0") is False
    assert is_newer_semver("1.3.0", None) is False


def test_sanitize_release_url() -> None:
    """Valida la sanitización estricta anti-open-redirect."""
    valid_url = f"{ALLOWED_GITHUB_RELEASE_PREFIX}/tag/v1.3.0"
    assert _sanitize_release_url(valid_url) == valid_url

    # URLs foráneas o esquemas javascript/maliciosos redirigen a la página segura por defecto
    assert _sanitize_release_url("https://malicious.evil/download") == DEFAULT_RELEASES_PAGE
    assert _sanitize_release_url("javascript:alert(1)") == DEFAULT_RELEASES_PAGE
    assert _sanitize_release_url(None) == DEFAULT_RELEASES_PAGE
    assert _sanitize_release_url("") == DEFAULT_RELEASES_PAGE


def test_decode_redis_val() -> None:
    """Valida decodificación segura de bytes o string."""
    assert _decode_redis_val(None) is None
    assert _decode_redis_val(b"hola") == "hola"
    assert _decode_redis_val("mundo") == "mundo"


@pytest.mark.asyncio
async def test_get_version_check_status_caching() -> None:
    """Verifica la lectura estructurada de KeyDB y recálculo en caliente."""
    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {
        b"latest_version": b"1.3.0",
        b"release_url": b"https://github.com/tecno-consultores/RoSGrid/releases/tag/v1.3.0",
        b"release_name": b"RoSGrid 1.3.0",
        b"published_at": b"2026-11-15T00:00:00Z",
        b"last_checked_at": b"2026-11-15T01:00:00Z",
        b"last_status": b"ok",
    }

    with patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis):
        status = await get_version_check_status()
        assert status["enabled"] is True
        assert status["latest_version"] == "1.3.0"
        assert status["update_available"] is True
        assert status["last_status"] == "ok"


@pytest.mark.asyncio
async def test_check_github_release_once_disabled() -> None:
    """Verifica que si la comprobación está deshabilitada no realiza petición HTTP."""
    with patch.object(settings, "ROSGRID_VERSION_CHECK_ENABLED", False):
        status = await check_github_release_once(force=False)
        assert status["enabled"] is False


@pytest.mark.asyncio
async def test_check_github_release_once_cooldown_active() -> None:
    """Verifica que el cooldown manual de 60s impida llamadas reiteradas a GitHub."""
    fake_redis = AsyncMock()
    fake_redis.exists.return_value = True

    with patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis):
        with patch("httpx.AsyncClient.get") as mock_get:
            status = await check_github_release_once(force=True)
            mock_get.assert_not_called()
            assert isinstance(status, dict)


@pytest.mark.asyncio
async def test_check_github_release_once_success_200() -> None:
    """Verifica el procesamiento exitoso de una nueva release pública."""
    fake_redis = AsyncMock()
    fake_redis.exists.return_value = False
    fake_redis.hgetall.return_value = {}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "tag_name": "v1.4.0",
        "name": "RoSGrid v1.4.0 Release",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-12-01T12:00:00Z",
        "html_url": "https://github.com/tecno-consultores/RoSGrid/releases/tag/v1.4.0",
    }

    with (
        patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)),
    ):
        status = await check_github_release_once(force=True)
        assert isinstance(status, dict)
        fake_redis.hset.assert_awaited()


@pytest.mark.asyncio
async def test_check_github_release_once_rate_limited_and_offline() -> None:
    """Verifica manejo fail-silent de rate limits y caídas de conectividad."""
    fake_redis = AsyncMock()
    fake_redis.exists.return_value = False
    fake_redis.hgetall.return_value = {}

    # Caso 429
    mock_429 = MagicMock()
    mock_429.status_code = 429

    with (
        patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_429)),
    ):
        status_429 = await check_github_release_once(force=False)
        assert isinstance(status_429, dict)

    # Caso error de red fail-silent
    with (
        patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis),
        patch("httpx.AsyncClient.get", AsyncMock(side_effect=httpx.ConnectError("Network unreachable"))),
    ):
        status_offline = await check_github_release_once(force=False)
        assert isinstance(status_offline, dict)


@pytest.mark.asyncio
async def test_version_check_worker_loop_graceful_shutdown() -> None:
    """Verifica que el ciclo del worker se detenga limpiamente ante stop_event."""
    stop_event = asyncio.Event()
    stop_event.set()

    # Debe retornar de inmediato en < 10ms
    await version_check_worker_loop(stop_event)

    # Cuando está deshabilitado
    with patch.object(settings, "ROSGRID_VERSION_CHECK_ENABLED", False):
        await version_check_worker_loop(None)


@pytest.mark.asyncio
async def test_system_version_check_api_endpoints() -> None:
    """Verifica los endpoints FastAPI en /api/v1/system."""
    fake_status = {
        "enabled": True,
        "current_version": "1.2.0",
        "latest_version": "1.3.0",
        "update_available": True,
        "release_url": "https://github.com/tecno-consultores/RoSGrid/releases",
        "release_name": "RoSGrid v1.3.0",
        "published_at": "2026-11-20T10:00:00Z",
        "last_checked_at": "2026-11-20T11:00:00Z",
        "last_status": "ok",
    }

    with patch("src.api.v1.system.get_version_check_status", AsyncMock(return_value=fake_status)):
        resp_get = await read_version_check_status()
        assert isinstance(resp_get, VersionCheckStatusResponse)
        assert resp_get.update_available is True
        assert resp_get.current_version == "1.2.0"

    with patch("src.api.v1.system.check_github_release_once", AsyncMock(return_value=fake_status)):
        resp_post = await trigger_version_check_refresh()
        assert isinstance(resp_post, VersionCheckStatusResponse)
        assert resp_post.latest_version == "1.3.0"


@pytest.mark.asyncio
async def test_version_check_worker_error_branches_and_sleep() -> None:
    """Verifica manejo de errores de Redis, respuestas http no 200 y helper de sleep."""
    from src.workers.version_check_worker import (
        _check_cooldown_active,
        _save_version_check_result,
        _version_sleep_interval,
    )

    # 1. Fallo en redis para save y cooldown
    with patch("src.workers.version_check_worker.get_redis_client", side_effect=RuntimeError("Redis down")):
        await _save_version_check_result("ok", {"tag_name": "v1.3.0"})
        in_cd = await _check_cooldown_active(force=True)
        assert in_cd is False

    # 2. _version_sleep_interval sin stop_event
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        slept = await _version_sleep_interval(None, 2)
        assert slept is False
        mock_sleep.assert_called_once_with(2)

    # 3. _version_sleep_interval timeout normal con stop_event
    event = asyncio.Event()
    with patch("asyncio.wait_for", AsyncMock(side_effect=TimeoutError())):
        slept_timeout = await _version_sleep_interval(event, 5)
        assert slept_timeout is False

    # 4. Prerelease o draft en release data
    fake_redis = MagicMock()
    fake_redis.hset = AsyncMock()
    fake_redis.hgetall = AsyncMock(return_value={})
    fake_redis.exists = AsyncMock(return_value=0)
    fake_redis.set = AsyncMock()

    mock_resp_draft = MagicMock()
    mock_resp_draft.status_code = 200
    mock_resp_draft.json.return_value = {"tag_name": "v1.4.0-rc1", "draft": True}

    with (
        patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp_draft)),
    ):
        st_draft = await check_github_release_once(force=False)
        assert isinstance(st_draft, dict)

    # 5. Status HTTP 500
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500
    with (
        patch("src.workers.version_check_worker.get_redis_client", return_value=fake_redis),
        patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp_500)),
    ):
        st_500 = await check_github_release_once(force=False)
        assert isinstance(st_500, dict)


@pytest.mark.asyncio
async def test_version_check_worker_loop_iteration() -> None:
    """Verifica que el bucle ejecute check_github_release_once y finalice en la siguiente evaluación."""
    stop_event = asyncio.Event()

    calls = 0

    async def _mock_sleep(event: Any, interval: int) -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            return False  # Permite entrar al loop
        return True  # Rompe el loop en la primera iteración

    with (
        patch("src.workers.version_check_worker._version_sleep_interval", side_effect=_mock_sleep),
        patch("src.workers.version_check_worker.check_github_release_once", AsyncMock()) as mock_check,
    ):
        await version_check_worker_loop(stop_event)
        mock_check.assert_called_once_with(force=False)
