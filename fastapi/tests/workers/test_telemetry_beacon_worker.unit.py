# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias para el Worker de Telemetría Anónima (Spec 55 / Hito 27.18)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.config import settings
from src.workers.telemetry_beacon_worker import (
    _count_active_routers_safe,
    _persist_beacon_state,
    compute_anonymous_instance_id,
    get_telemetry_beacon_status,
    resolve_fleet_bucket,
    send_telemetry_heartbeat_once,
    telemetry_beacon_worker_loop,
)


def test_compute_anonymous_instance_id_format() -> None:
    """Certifica que el instance_id generado sea exactamente un hash SHA-256 de 64 caracteres hex."""
    instance_id = compute_anonymous_instance_id("test-secret-key-seed")
    assert len(instance_id) == 64
    assert all(c in "0123456789abcdef" for c in instance_id)

    # Determinismo
    assert compute_anonymous_instance_id("test-secret-key-seed") == instance_id
    # No colisión con otra semilla
    assert compute_anonymous_instance_id("other-seed") != instance_id
    # Fallback con semilla vacía
    empty_seed_id = compute_anonymous_instance_id("")
    assert len(empty_seed_id) == 64


def test_resolve_fleet_bucket_ranges() -> None:
    """Certifica que el agrupador de flota categorice correctamente sin revelar datos exactos."""
    assert resolve_fleet_bucket(0) == "0"
    assert resolve_fleet_bucket(-5) == "0"
    assert resolve_fleet_bucket(1) == "1-10"
    assert resolve_fleet_bucket(10) == "1-10"
    assert resolve_fleet_bucket(11) == "11-50"
    assert resolve_fleet_bucket(50) == "11-50"
    assert resolve_fleet_bucket(51) == "51-250"
    assert resolve_fleet_bucket(250) == "51-250"
    assert resolve_fleet_bucket(251) == "250+"
    assert resolve_fleet_bucket(1000) == "250+"


@pytest.mark.asyncio
async def test_count_active_routers_safe_success() -> None:
    """Verifica el conteo de routers cuando la base de datos responde exitosamente activando RLS SuperAdmin."""
    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar.return_value = 5
    mock_session.execute = AsyncMock(return_value=mock_res)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("src.workers.telemetry_beacon_worker.async_session_maker", return_value=mock_cm),
        patch("src.workers.telemetry_beacon_worker.set_tenant_context", new_callable=AsyncMock) as mock_set_tenant,
    ):
        count = await _count_active_routers_safe()
        assert count == 5
        mock_set_tenant.assert_awaited_once_with(mock_session, None, is_superadmin=True)


@pytest.mark.asyncio
async def test_count_active_routers_safe_exception_fail_silent() -> None:
    """Verifica que un fallo de base de datos no arroje excepción y retorne 0 fail-silent."""
    with patch("src.workers.telemetry_beacon_worker.async_session_maker", side_effect=Exception("DB Down")):
        count = await _count_active_routers_safe()
        assert count == 0


@pytest.mark.asyncio
async def test_persist_beacon_state_and_redis_error_resilience() -> None:
    """Verifica la persistencia en KeyDB y la tolerancia cuando KeyDB falla."""
    mock_redis = AsyncMock()
    with patch("src.workers.telemetry_beacon_worker.get_redis_client", return_value=mock_redis):
        await _persist_beacon_state("hash64", "2026-11-01T00:00:00Z", "sent", fleet_bucket="1-10", router_count=5)
        mock_redis.hset.assert_awaited_once()

    # Si redis falla, debe ser fail-silent
    with patch("src.workers.telemetry_beacon_worker.get_redis_client", side_effect=Exception("Redis error")):
        await _persist_beacon_state("hash64", "2026-11-01T00:00:00Z", "sent", fleet_bucket="1-10", router_count=5)


@pytest.mark.asyncio
async def test_get_telemetry_beacon_status_with_and_without_state() -> None:
    """Verifica la obtención de estado con y sin datos previos en KeyDB incluyendo fleet_bucket y router_count."""
    # Sin datos en KeyDB
    mock_redis = AsyncMock()
    mock_redis.hgetall.return_value = {}
    with (
        patch("src.workers.telemetry_beacon_worker.get_redis_client", return_value=mock_redis),
        patch("src.workers.telemetry_beacon_worker._count_active_routers_safe", return_value=7),
    ):
        status = await get_telemetry_beacon_status()
        assert status["enabled"] is False
        assert len(status["instance_id"]) == 64
        assert status["last_sent_at"] is None
        assert status["last_heartbeat_at"] is None
        assert status["last_status"] == "untriggered"
        assert status["fleet_bucket"] == "1-10"
        assert status["router_count"] == 7

    # Con datos previos
    mock_redis.hgetall.return_value = {
        "instance_id": "custom_instance_id",
        "last_sent_at": "2026-11-01T12:00:00Z",
        "last_status": "http_202",
        "fleet_bucket": "11-50",
    }
    with (
        patch("src.workers.telemetry_beacon_worker.get_redis_client", return_value=mock_redis),
        patch("src.workers.telemetry_beacon_worker._count_active_routers_safe", return_value=15),
    ):
        status = await get_telemetry_beacon_status()
        assert status["instance_id"] == "custom_instance_id"
        assert status["last_sent_at"] == "2026-11-01T12:00:00Z"
        assert status["last_heartbeat_at"] == "2026-11-01T12:00:00Z"
        assert status["last_status"] == "http_202"
        assert status["fleet_bucket"] == "11-50"
        assert status["router_count"] == 15


@pytest.mark.asyncio
async def test_send_telemetry_heartbeat_once_disabled() -> None:
    """Certifica que si el beacon está deshabilitado no se realice ninguna llamada HTTP."""
    with patch.object(settings, "ROSGRID_TELEMETRY_BEACON_ENABLED", False):
        res = await send_telemetry_heartbeat_once(router_count=3)
        assert res["enabled"] is False
        assert res["last_status"] == "disabled"


@pytest.mark.asyncio
async def test_send_telemetry_heartbeat_once_success_http_202() -> None:
    """Certifica el envío exitoso del latido y su registro de estado http_202."""
    mock_resp = MagicMock()
    mock_resp.status_code = 202

    with (
        patch.object(settings, "ROSGRID_TELEMETRY_BEACON_ENABLED", True),
        patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post,
        patch("src.workers.telemetry_beacon_worker._persist_beacon_state", new_callable=AsyncMock) as mock_persist,
    ):
        res = await send_telemetry_heartbeat_once(router_count=15)
        assert res["enabled"] is True
        assert res["last_status"] == "http_202"
        assert res["fleet_bucket"] == "11-50"
        assert res["router_count"] == 15
        assert res["last_heartbeat_at"] == res["last_sent_at"]
        mock_post.assert_awaited_once()
        mock_persist.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_telemetry_heartbeat_once_waf_403_fallback_to_get() -> None:
    """Certifica que ante un bloqueo WAF 403 en POST se realice fallback automático a GET con estado http_202."""
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 403
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 202

    with (
        patch.object(settings, "ROSGRID_TELEMETRY_BEACON_ENABLED", True),
        patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_post_resp) as mock_post,
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_get_resp) as mock_get,
        patch("src.workers.telemetry_beacon_worker._persist_beacon_state", new_callable=AsyncMock) as mock_persist,
    ):
        res = await send_telemetry_heartbeat_once(router_count=7)
        assert res["enabled"] is True
        assert res["last_status"] == "http_202"
        assert res["fleet_bucket"] == "1-10"
        mock_post.assert_awaited_once()
        mock_get.assert_awaited_once()
        mock_persist.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_telemetry_heartbeat_once_network_error_fail_silent() -> None:
    """Certifica que un fallo de red o timeout sea fail-silent y marque offline_skipped."""
    with (
        patch.object(settings, "ROSGRID_TELEMETRY_BEACON_ENABLED", True),
        patch("httpx.AsyncClient.post", side_effect=Exception("Connect timeout")),
        patch("src.workers.telemetry_beacon_worker._persist_beacon_state", new_callable=AsyncMock) as mock_persist,
    ):
        res = await send_telemetry_heartbeat_once(router_count=5)
        assert res["enabled"] is True
        assert res["last_status"] == "offline_skipped"
        assert res["fleet_bucket"] == "1-10"
        mock_persist.assert_awaited_once()


@pytest.mark.asyncio
async def test_telemetry_beacon_worker_loop_disabled() -> None:
    """Certifica que el worker loop salga de inmediato si está deshabilitado."""
    with (
        patch.object(settings, "ROSGRID_TELEMETRY_BEACON_ENABLED", False),
        patch("src.workers.telemetry_beacon_worker.send_telemetry_heartbeat_once", new_callable=AsyncMock) as mock_send,
    ):
        await telemetry_beacon_worker_loop()
        mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_telemetry_beacon_worker_loop_clean_stop() -> None:
    """Certifica que el worker loop se detenga inmediatamente cuando stop_event se active."""
    stop_event = asyncio.Event()
    stop_event.set()

    with (
        patch.object(settings, "ROSGRID_TELEMETRY_BEACON_ENABLED", True),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("src.workers.telemetry_beacon_worker.send_telemetry_heartbeat_once", new_callable=AsyncMock) as mock_send,
    ):
        await telemetry_beacon_worker_loop(stop_event=stop_event)
        assert stop_event.is_set() is True
        mock_send.assert_not_awaited()
