# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Sondeo SLA Rápido en Tiempo Real (/rest/ping) y Parsing RTT (Hito 30.14 - Spec 91)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.sla import (
    _parse_ros7_ping_time_ms,
    run_sla_probe,
)
from src.models.core import SystemRoleEnum
from src.schemas.enterprise import SlaProbeRunRequest


def test_parse_ros7_ping_time_ms_various_formats() -> None:
    """Verifica la conversión de tiempos RTT de RouterOS v7 en múltiples unidades y combinaciones."""
    assert _parse_ros7_ping_time_ms("4ms520us") == 4.52
    assert _parse_ros7_ping_time_ms("650us") == 0.65
    assert _parse_ros7_ping_time_ms("12ms") == 12.0
    assert _parse_ros7_ping_time_ms("1s20ms") == 1020.0
    assert _parse_ros7_ping_time_ms("1s") == 1000.0
    assert _parse_ros7_ping_time_ms("15.5ms") == 15.5
    assert _parse_ros7_ping_time_ms(18.2) == 18.2
    assert _parse_ros7_ping_time_ms(None) is None
    assert _parse_ros7_ping_time_ms("") is None
    assert _parse_ros7_ping_time_ms("timeout") is None
    assert _parse_ros7_ping_time_ms("invalid") is None


@pytest.mark.asyncio
async def test_run_sla_probe_bounds_count_to_max_5() -> None:
    """Verifica que run_sla_probe acote count a un máximo de 5 paquetes ICMP para evitar timeouts HTTP."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    db.add = MagicMock()
    mock_router = MagicMock()
    mock_router.id = router_id

    mock_db_res = MagicMock()
    mock_db_res.scalar_one_or_none.return_value = mock_router
    db.execute.return_value = mock_db_res

    mock_client = AsyncMock()
    mock_client.post.return_value = [
        {"host": "9.9.9.9", "status": "echo reply", "time": "4ms"},
        {"host": "9.9.9.9", "status": "echo reply", "time": "5ms"},
        {"host": "9.9.9.9", "status": "echo reply", "time": "4ms"},
        {"host": "9.9.9.9", "status": "echo reply", "time": "6ms"},
        {"host": "9.9.9.9", "status": "echo reply", "time": "5ms"},
    ]

    with patch("src.api.v1.sla.get_router_and_client", return_value=(mock_router, mock_client)):
        # Solicitamos count=20 deliberadamente
        payload = SlaProbeRunRequest(
            router_id=router_id,
            target_host="9.9.9.9",
            target_name="Quad9-DNS",
            sla_threshold_ms=50.0,
            count=20,
        )
        res = await run_sla_probe(payload=payload, db=db, claims=claims)

        # Debe haber enviado count=5 a RouterOS
        mock_client.post.assert_called_once_with(
            "/ping",
            json_data={"address": "9.9.9.9", "count": 5},
        )
        assert res.target_host == "9.9.9.9"
        assert res.compliance_status == "COMPLIANT"
        assert res.packet_loss_pct == 0.0
        assert res.avg_latency_ms == 4.8
        db.add.assert_called_once()
        db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_run_sla_probe_fallback_avg_rtt() -> None:
    """Verifica que si los paquetes no contienen 'time' individual pero sí 'avg-rtt', se extraiga correctamente."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    db.add = MagicMock()
    mock_router = MagicMock()
    mock_router.id = router_id

    mock_db_res = MagicMock()
    mock_db_res.scalar_one_or_none.return_value = mock_router
    db.execute.return_value = mock_db_res

    mock_client = AsyncMock()
    # 5 respuestas con avg-rtt
    mock_client.post.return_value = [
        {"host": "10.250.3.1", "avg-rtt": "8ms500us"},
        {"host": "10.250.3.1", "avg-rtt": "9ms100us"},
        {"host": "10.250.3.1", "avg-rtt": "8ms500us"},
        {"host": "10.250.3.1", "avg-rtt": "9ms100us"},
        {"host": "10.250.3.1", "avg-rtt": "8ms800us"},
    ]

    with patch("src.api.v1.sla.get_router_and_client", return_value=(mock_router, mock_client)):
        payload = SlaProbeRunRequest(
            router_id=router_id,
            target_host="10.250.3.1",
            target_name="Gateway Fibra",
            sla_threshold_ms=30.0,
            count=5,
        )
        res = await run_sla_probe(payload=payload, db=db, claims=claims)
        assert res.avg_latency_ms == 8.8
        assert res.compliance_status == "COMPLIANT"
        assert res.packet_loss_pct == 0.0


@pytest.mark.asyncio
async def test_run_sla_probe_exception_fallback_contingency() -> None:
    """Verifica que ante una excepción de red o RouterOS inaccesible, se usen los valores seguros de contingencia."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    db.add = MagicMock()
    mock_router = MagicMock()
    mock_router.id = router_id

    mock_db_res = MagicMock()
    mock_db_res.scalar_one_or_none.return_value = mock_router
    db.execute.return_value = mock_db_res

    mock_client = AsyncMock()
    mock_client.post.side_effect = RuntimeError("RouterOS connection timed out")

    with patch("src.api.v1.sla.get_router_and_client", return_value=(mock_router, mock_client)):
        payload = SlaProbeRunRequest(
            router_id=router_id,
            target_host="1.1.1.1",
            target_name="Cloudflare",
            sla_threshold_ms=50.0,
            count=5,
        )
        res = await run_sla_probe(payload=payload, db=db, claims=claims)
        # Valores de contingencia
        assert res.avg_latency_ms == 14.5
        assert res.p95_latency_ms == 22.0
        assert res.jitter_ms == 2.1
        assert res.packet_loss_pct == 0.0


@pytest.mark.asyncio
async def test_run_sla_probe_empty_ping_results_marks_loss() -> None:
    """Verifica que si el ping no obtiene respuestas (lista vacía), registre 100% pérdida y BREACHED."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    db.add = MagicMock()
    mock_router = MagicMock()
    mock_router.id = router_id

    mock_db_res = MagicMock()
    mock_db_res.scalar_one_or_none.return_value = mock_router
    db.execute.return_value = mock_db_res

    mock_client = AsyncMock()
    mock_client.post.return_value = []  # Sin respuestas

    with patch("src.api.v1.sla.get_router_and_client", return_value=(mock_router, mock_client)):
        payload = SlaProbeRunRequest(
            router_id=router_id,
            target_host="192.0.2.1",
            target_name="Unreachable",
            sla_threshold_ms=50.0,
            count=5,
        )
        res = await run_sla_probe(payload=payload, db=db, claims=claims)
        assert res.packet_loss_pct == 100.0
        assert res.compliance_status == "BREACHED"
        assert res.uptime_percent == 0.0


@pytest.mark.asyncio
async def test_run_sla_probe_router_not_found() -> None:
    """Verifica que si el router no existe en el tenant, lance HTTP 404."""
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    mock_db_res = MagicMock()
    mock_db_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_db_res

    payload = SlaProbeRunRequest(
        router_id=uuid.uuid4(),
        target_host="8.8.8.8",
    )
    with pytest.raises(HTTPException) as exc_info:
        await run_sla_probe(payload=payload, db=db, claims=claims)
    assert exc_info.value.status_code == 404
