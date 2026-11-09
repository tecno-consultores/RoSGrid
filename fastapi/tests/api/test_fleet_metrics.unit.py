# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.fleet_metrics import (
    _append_router_metrics,
    _build_router_labels,
    _extract_raw_temp,
    _extract_raw_uptime,
    _extract_raw_voltage,
    _format_metric_line,
    _get_router_ephemeral_telemetry,
    _parse_ros_uptime_to_seconds,
    _safe_float,
    _safe_int,
    _validate_scrape_auth,
    get_prometheus_fleet_metrics,
)
from src.core.config import settings
from src.models.inventory import Router


def test_parse_ros_uptime_to_seconds():
    # Null and empty
    assert _parse_ros_uptime_to_seconds(None) == 0
    assert _parse_ros_uptime_to_seconds("") == 0
    assert _parse_ros_uptime_to_seconds("   ") == 0

    # Numeric strings and ints
    assert _parse_ros_uptime_to_seconds("12345") == 12345
    assert _parse_ros_uptime_to_seconds(98765) == 98765

    # Individual units
    assert _parse_ros_uptime_to_seconds("1w") == 604800
    assert _parse_ros_uptime_to_seconds("2d") == 172800
    assert _parse_ros_uptime_to_seconds("3h") == 10800
    assert _parse_ros_uptime_to_seconds("4m") == 240
    assert _parse_ros_uptime_to_seconds("5s") == 5

    # Compound RouterOS uptime string
    # 2w (1209600) + 3d (259200) + 4h (14400) + 5m (300) + 6s (6) = 1483506
    assert _parse_ros_uptime_to_seconds("2w3d4h5m6s") == 1483506
    assert _parse_ros_uptime_to_seconds("  1W2D  ") == 604800 + 172800

    # Non-matching string
    assert _parse_ros_uptime_to_seconds("unsupported_string") == 0


def test_safe_helpers():
    # _safe_float
    assert _safe_float(3.14) == 3.14
    assert _safe_float("42.5") == 42.5
    assert _safe_float(None, 10.0) == 10.0
    assert _safe_float("invalid", 5.0) == 5.0

    # _safe_int
    assert _safe_int(10) == 10
    assert _safe_int("20") == 20
    assert _safe_int(None, 7) == 7
    assert _safe_int("invalid", 3) == 3


def test_extract_telemetry_fields():
    # _extract_raw_uptime
    assert _extract_raw_uptime({"uptime_seconds": 3600}) == 3600
    assert _extract_raw_uptime({"uptime": "1h"}) == 3600
    assert _extract_raw_uptime({}) == 0

    # _extract_raw_temp
    assert _extract_raw_temp({"temperature_celsius": "45.2"}) == 45.2
    assert _extract_raw_temp({"temperature": "43.0"}) == 43.0
    assert _extract_raw_temp({"cpu_temperature": 52.1}) == 52.1
    assert _extract_raw_temp({}) == 0.0

    # _extract_raw_voltage
    assert _extract_raw_voltage({"voltage_volts": "24.1"}) == 24.1
    assert _extract_raw_voltage({"voltage": 12.0}) == 12.0
    assert _extract_raw_voltage({}) == 0.0


def test_build_router_labels():
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    r = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="Edge-01",
        ros_identity="Edge-NOC",
        model_name="RB5009UG+S+IN",
        ros_version="7.16.2",
    )
    labels = _build_router_labels(r)
    assert labels["tenant_id"] == str(t_id)
    assert labels["router_id"] == str(r_id)
    assert labels["identity"] == "Edge-NOC"
    assert labels["model"] == "RB5009UG+S+IN"
    assert labels["ros_version"] == "7.16.2"

    # Router with fallback identity and missing version/model
    r_fallback = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="Fallback-Display",
        ros_identity=None,
        model_name=None,
        ros_version=None,
    )
    labels_fallback = _build_router_labels(r_fallback)
    assert labels_fallback["identity"] == "Fallback-Display"
    assert labels_fallback["model"] == "unknown"
    assert labels_fallback["ros_version"] == "unknown"


def test_format_metric_line():
    line = _format_metric_line("test_metric", {"env": "prod", "code": "200"}, 1)
    assert line == 'test_metric{env="prod",code="200"} 1\n'


def test_validate_scrape_auth_matrix():
    with patch.object(settings, "ROSGRID_PROMETHEUS_SCRAPE_TOKEN", ""):
        _validate_scrape_auth(None)
        _validate_scrape_auth("Bearer whatever")

    with patch.object(settings, "ROSGRID_PROMETHEUS_SCRAPE_TOKEN", "super-secret-token"):
        # Valid
        _validate_scrape_auth("Bearer super-secret-token")

        # Missing
        with pytest.raises(HTTPException) as exc1:
            _validate_scrape_auth(None)
        assert exc1.value.status_code == 401

        # Not bearer
        with pytest.raises(HTTPException) as exc2:
            _validate_scrape_auth("Token 12345")
        assert exc2.value.status_code == 401

        # Invalid token
        with pytest.raises(HTTPException) as exc3:
            _validate_scrape_auth("Bearer wrong-token")
        assert exc3.value.status_code == 401


@pytest.mark.asyncio
async def test_get_router_ephemeral_telemetry():
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {
        "cpu_percent": "28.5",
        "memory_usage_ratio": "0.55",
        "uptime": "3d12h",
        "temperature_celsius": "48.0",
        "voltage_volts": "24.2",
        "syslog_critical_events_total": "3",
    }

    with patch("src.api.v1.fleet_metrics.get_redis_client", return_value=fake_redis):
        data = await _get_router_ephemeral_telemetry(t_id, r_id)
        assert data["cpu_percent"] == 28.5
        assert data["memory_usage_ratio"] == 0.55
        assert data["uptime_seconds"] == (3 * 86400) + (12 * 3600)
        assert data["temperature_celsius"] == 48.0
        assert data["voltage_volts"] == 24.2
        assert data["syslog_critical_events_total"] == 3

    # Empty redis state
    fake_redis.hgetall.return_value = {}
    with patch("src.api.v1.fleet_metrics.get_redis_client", return_value=fake_redis):
        empty_data = await _get_router_ephemeral_telemetry(t_id, r_id)
        assert empty_data["cpu_percent"] == 0.0
        assert empty_data["uptime_seconds"] == 0

    # Redis error tolerance
    fake_redis.hgetall.side_effect = Exception("Redis connection refused")
    with patch("src.api.v1.fleet_metrics.get_redis_client", return_value=fake_redis):
        err_data = await _get_router_ephemeral_telemetry(t_id, r_id)
        assert err_data["cpu_percent"] == 0.0
        assert err_data["temperature_celsius"] == 0.0


def test_append_router_metrics():
    r = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="Core-CCR",
        ros_identity="CCR-NOC",
        model_name="CCR2004",
        ros_version="7.16",
        is_reachable=True,
    )
    telem = {
        "cpu_percent": 12.5,
        "memory_usage_ratio": 0.35,
        "uptime_seconds": 90000,
        "temperature_celsius": 42.0,
        "voltage_volts": 24.0,
        "syslog_critical_events_total": 1,
    }
    lines: list[str] = []
    _append_router_metrics(lines, r, telem)
    text = "".join(lines)

    assert 'rosgrid_router_status{tenant_id="' in text
    assert 'ros_version="7.16"' in text
    assert "rosgrid_router_cpu_percent" in text
    assert "rosgrid_router_memory_usage_ratio" in text
    assert "rosgrid_router_uptime_seconds" in text
    assert "rosgrid_router_temperature_celsius" in text
    assert "rosgrid_router_voltage_volts" in text
    assert 'severity="critical"' in text
    assert 'severity="high"' in text
    assert "rosgrid_router_syslog_critical_events_total" in text


@pytest.mark.asyncio
async def test_get_prometheus_fleet_metrics_full_response():
    db = AsyncMock()
    r1 = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="Router-Alpha",
        ros_identity="Alpha-NOC",
        model_name="RB4011",
        ros_version="7.15.3",
        is_reachable=True,
        admin_state="PRODUCTION",
    )
    r2 = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="Router-Beta",
        ros_identity="Beta-NOC",
        model_name="CRS326",
        ros_version="7.12",
        is_reachable=False,
        admin_state="PRODUCTION",
    )
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [r1, r2]
    db.execute.return_value = mock_res

    fake_redis = AsyncMock()
    fake_redis.hgetall.return_value = {
        "cpu_percent": "18.0",
        "memory_usage_ratio": "0.45",
        "uptime_seconds": "86400",
        "temperature_celsius": "41.5",
        "voltage_volts": "24.0",
        "syslog_critical_events_total": "0",
    }

    with patch("src.api.v1.fleet_metrics.get_redis_client", return_value=fake_redis):
        resp = await get_prometheus_fleet_metrics(db=db)
        assert resp.status_code == 200
        assert resp.media_type == "text/plain; version=0.0.4; charset=utf-8"

        body = resp.body.decode("utf-8")
        # All 8 metric names must be documented in headers and present in body
        assert "rosgrid_router_status" in body
        assert "rosgrid_router_cpu_percent" in body
        assert "rosgrid_router_memory_usage_ratio" in body
        assert "rosgrid_router_uptime_seconds" in body
        assert "rosgrid_router_temperature_celsius" in body
        assert "rosgrid_router_voltage_volts" in body
        assert "rosgrid_router_active_cves_count" in body
        assert "rosgrid_router_syslog_critical_events_total" in body

        # Reachability status check
        assert 'rosgrid_router_status{tenant_id="' in body
        assert 'identity="Alpha-NOC"' in body
        assert 'identity="Beta-NOC"' in body
