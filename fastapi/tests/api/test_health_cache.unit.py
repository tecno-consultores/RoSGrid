# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint_cached(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que el endpoint /health responda correctamente y que la caché en memoria funcione."""
    import src.main as main_mod
    from src.core.config import settings

    # Simular entorno de producción para habilitar TTL > 0
    monkeypatch.setattr(settings, "ROSGRID_ENV", "production")
    main_mod._last_health_check_time = 0.0
    main_mod._cached_health_payload = {}
    main_mod._cached_status_code = 200

    mock_db = AsyncMock(return_value="connected")
    mock_redis = AsyncMock(return_value="connected")
    monkeypatch.setattr(main_mod, "_check_database_health", mock_db)
    monkeypatch.setattr(main_mod, "_check_redis_health", mock_redis)

    res1 = await async_client.get("/health")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "healthy"
    assert data1["service"] == "rosgrid-api"
    assert mock_db.call_count == 1
    assert mock_redis.call_count == 1

    # Segunda llamada inmediata: debe responder desde la caché sin invocar db o redis de nuevo
    res2 = await async_client.get("/health")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2 == data1
    assert mock_db.call_count == 1
    assert mock_redis.call_count == 1

    # Forzar refresco con force=True
    res_forced = await async_client.get("/health?force=true")
    assert res_forced.status_code == 200
    assert mock_db.call_count == 2
    assert mock_redis.call_count == 2


@pytest.mark.asyncio
async def test_health_check_cache_degraded(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que si el sistema está degradado la caché recuerde el código 503."""
    import src.main as main_mod
    from src.core.config import settings

    monkeypatch.setattr(settings, "ROSGRID_ENV", "production")
    main_mod._last_health_check_time = 0.0
    main_mod._cached_health_payload = {}

    mock_db = AsyncMock(return_value="connected")
    mock_redis = AsyncMock(return_value="disconnected")
    monkeypatch.setattr(main_mod, "_check_database_health", mock_db)
    monkeypatch.setattr(main_mod, "_check_redis_health", mock_redis)

    res = await async_client.get("/health")
    assert res.status_code == 503
    data = res.json()
    assert data["status"] == "unhealthy"
    assert data["redis"] == "disconnected"
    assert mock_redis.call_count == 1

    # Segunda llamada: retorna 503 desde la caché sin re-evaluar
    res_cached = await async_client.get("/health")
    assert res_cached.status_code == 503
    assert res_cached.json()["status"] == "unhealthy"
    assert mock_redis.call_count == 1
