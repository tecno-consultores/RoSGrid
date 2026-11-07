# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Detección de Anomalías de Tráfico y Mitigación FastDrop (Hito 30.14 - Spec 91)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.traffic_flow import (
    _aggregate_connection_stats,
    _analyze_connections,
    _extract_ip_from_address,
    _is_valid_anomaly_source_ip,
    detect_traffic_anomalies,
    mitigate_traffic_anomaly,
)
from src.models.core import SystemRoleEnum
from src.schemas.traffic_flow import TrafficMitigationRequest


def test_is_valid_anomaly_source_ip_rejects_unroutable_and_special() -> None:
    """Valida que direcciones no enrutables, loopback, link-local, multicast y broadcast sean rechazadas."""
    unroutable_ips = [
        "",
        "   ",
        "0.0.0.0",
        "255.255.255.255",
        "::",
        "::1",
        "127.0.0.1",
        "127.0.0.53",
        "169.254.1.10",
        "169.254.169.254",
        "fe80::1",
        "fe80::dead:beef",
        "224.0.0.1",
        "224.0.0.5",
        "239.255.255.250",
        "ff02::1",
        "240.0.0.1",  # RFC 1112 reserved
        "invalid-ip-string",
    ]
    for ip in unroutable_ips:
        assert not _is_valid_anomaly_source_ip(ip), f"La IP '{ip}' debió ser rechazada por no ser enrutable"


def test_is_valid_anomaly_source_ip_rejects_local_router_ips() -> None:
    """Valida que las IPs asignadas a las interfaces del router sean excluidas."""
    local_ips = {"10.250.3.20", "192.168.88.1", "172.16.0.1"}
    for lip in local_ips:
        assert not _is_valid_anomaly_source_ip(lip, local_router_ips=local_ips)


def test_is_valid_anomaly_source_ip_accepts_valid_hosts() -> None:
    """Valida que direcciones de hosts válidas (privadas y públicas) sean aceptadas."""
    valid_ips = [
        "192.168.88.10",
        "10.0.4.15",
        "172.20.10.5",
        "8.8.8.8",
        "1.1.1.1",
        "203.0.113.195",
        "2001:db8::1",
    ]
    for ip in valid_ips:
        assert _is_valid_anomaly_source_ip(ip), f"La IP '{ip}' debió ser aceptada como host válido"


def test_extract_ip_from_address() -> None:
    """Verifica que el extractor de IP elimine puertos correctamente."""
    assert _extract_ip_from_address("192.168.1.100:443") == "192.168.1.100"
    assert _extract_ip_from_address("10.0.0.1") == "10.0.0.1"
    assert _extract_ip_from_address("  172.16.0.5:8080  ") == "172.16.0.5"


def test_aggregate_connection_stats_excludes_unroutable_and_local() -> None:
    """Verifica que conexiones con 0.0.0.0, 127.0.0.1, link-local o IP del router no ingresen a las estadísticas."""
    local_router_ips = {"10.250.3.20"}
    raw_conns = [
        {"src-address": "0.0.0.0:68", "protocol": "udp", "orig-packets": 500},
        {"src-address": "255.255.255.255:67", "protocol": "udp", "orig-packets": 500},
        {"src-address": "127.0.0.1:53", "protocol": "tcp", "orig-packets": 2000},
        {"src-address": "169.254.10.20:1234", "protocol": "tcp", "orig-packets": 1000},
        {"src-address": "10.250.3.20:443", "protocol": "tcp", "orig-packets": 3000},  # Router IP
        {"src-address": "198.51.100.99:51234", "protocol": "tcp", "orig-packets": 150},  # Atacante
    ]
    stats = _aggregate_connection_stats(raw_conns, local_router_ips=local_router_ips)
    assert "0.0.0.0" not in stats
    assert "255.255.255.255" not in stats
    assert "127.0.0.1" not in stats
    assert "169.254.10.20" not in stats
    assert "10.250.3.20" not in stats
    assert "198.51.100.99" in stats
    assert stats["198.51.100.99"]["count"] == 1


def test_analyze_connections_single_persistent_session_no_false_positive() -> None:
    """Verifica que una sesión persistente única con muchos paquetes acumulados no dispare HIGH_PPS_BURST."""
    # Una única conexión de SSH o BGP con 50,000 paquetes acumulados a lo largo de días
    raw_conns = [
        {"src-address": "192.168.1.50:22", "protocol": "tcp", "orig-packets": 50000}
    ]
    anomalies = _analyze_connections(raw_conns, threshold_pps=1000, threshold_conns=500)
    assert len(anomalies) == 0, "No debe disparar falso positivo de ráfaga PPS en una única sesión aislada"


def test_analyze_connections_detects_real_flood() -> None:
    """Verifica que ráfagas con múltiples conexiones o tasa real orig-rate sean detectadas correctamente."""
    # Atacante con 5 conexiones y alta tasa
    raw_conns = [
        {"src-address": "203.0.113.80:1001", "protocol": "udp", "orig-packets": 20000},
        {"src-address": "203.0.113.80:1002", "protocol": "udp", "orig-packets": 20000},
        {"src-address": "203.0.113.80:1003", "protocol": "udp", "orig-packets": 20000},
        {"src-address": "203.0.113.80:1004", "protocol": "udp", "orig-packets": 20000},
    ]
    anomalies = _analyze_connections(raw_conns, threshold_pps=1000, threshold_conns=500)
    assert len(anomalies) == 1
    assert anomalies[0].ip_address == "203.0.113.80"
    assert anomalies[0].anomaly_type == "HIGH_PPS_BURST"
    assert anomalies[0].severity in ("HIGH", "CRITICAL")


@pytest.mark.asyncio
async def test_detect_traffic_anomalies_filters_router_own_ip_and_zero_ip() -> None:
    """Verifica que detect_traffic_anomalies excluya 0.0.0.0 y las IPs propias de las interfaces del router."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()

    mock_client = AsyncMock()
    # /ip/firewall/connection contiene 0.0.0.0:68 y la IP local del router 10.250.3.20:443
    mock_client.get.side_effect = [
        [
            {"src-address": "0.0.0.0:68", "protocol": "udp", "orig-packets": 5000},
            {"src-address": "10.250.3.20:443", "protocol": "tcp", "orig-packets": 9000},
        ],  # /ip/firewall/connection
        [
            {"address": "10.250.3.20/24", "interface": "ether1"},
            {"address": "192.168.88.1/24", "interface": "bridge"},
        ],  # /ip/address
    ]
    mock_router_obj = MagicMock()
    mock_router_obj.id = router_id
    mock_router_obj.display_name = "Core-Edge-01"

    with patch("src.api.v1.traffic_flow.get_router_and_client", return_value=(mock_router_obj, mock_client)):
        res = await detect_traffic_anomalies(
            router_id=router_id,
            threshold_pps=500,
            threshold_conns=100,
            claims=claims,
            db=db,
        )
        # Ambas deben haber sido filtradas
        assert res.anomalies_detected == 0
        assert len(res.items) == 0


@pytest.mark.asyncio
async def test_mitigate_traffic_anomaly_rejects_unroutable_ip_422() -> None:
    """Verifica que POST /api/v1/traffic-flow/mitigate lance HTTP 422 ante IPs no enrutables o reservadas."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    mock_request = MagicMock()

    invalid_targets = ["0.0.0.0", "127.0.0.1", "255.255.255.255", "169.254.1.1", "224.0.0.5", "::1"]
    for inv_ip in invalid_targets:
        payload = TrafficMitigationRequest(
            router_id=router_id,
            target_ip=inv_ip,
            action="fast_drop",
            comment="Mitigate Test",
            duration_seconds=300,
        )
        with pytest.raises(HTTPException) as exc_info:
            await mitigate_traffic_anomaly(
                payload=payload,
                request=mock_request,
                claims=claims,
                db=db,
            )
        assert exc_info.value.status_code == 422
        assert "Dirección IP reservada o inválida" in exc_info.value.detail


@pytest.mark.asyncio
async def test_mitigate_traffic_anomaly_success_fast_drop() -> None:
    """Verifica que POST /api/v1/traffic-flow/mitigate ejecute FastDrop y registre auditoría WORM."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    mock_router = MagicMock()
    mock_router.id = router_id
    mock_router.display_name = "Core-Edge-01"

    mock_client = AsyncMock()
    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.99"
    mock_request.headers.get.return_value = "Pytest/1.0"

    with (
        patch("src.api.v1.traffic_flow.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.traffic_flow.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.traffic_flow.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        payload = TrafficMitigationRequest(
            router_id=router_id,
            target_ip="198.51.100.77",
            action="fast_drop",
            comment="FastDrop Anomaly",
            duration_seconds=300,
        )
        res = await mitigate_traffic_anomaly(
            payload=payload,
            request=mock_request,
            claims=claims,
            db=db,
        )
        assert res.status == "MITIGATED"
        assert res.target_ip == "198.51.100.77"
        assert res.action_taken == "fast_drop"
        assert res.safemode_applied is True
        mock_audit.assert_called_once()
        db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mitigate_traffic_anomaly_success_blackhole() -> None:
    """Verifica que POST /api/v1/traffic-flow/mitigate ejecute ruta Blackhole y registre auditoría WORM."""
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()
    mock_router = MagicMock()
    mock_router.id = router_id
    mock_router.display_name = "Core-Edge-01"

    mock_client = AsyncMock()
    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.99"
    mock_request.headers.get.return_value = "Pytest/1.0"

    with (
        patch("src.api.v1.traffic_flow.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.traffic_flow.execute_safe_mutation", return_value={"ret": "*2"}),
        patch("src.api.v1.traffic_flow.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        payload = TrafficMitigationRequest(
            router_id=router_id,
            target_ip="198.51.100.88",
            action="blackhole",
            comment="Blackhole route mitigation",
            duration_seconds=600,
        )
        res = await mitigate_traffic_anomaly(
            payload=payload,
            request=mock_request,
            claims=claims,
            db=db,
        )
        assert res.status == "MITIGATED"
        assert res.target_ip == "198.51.100.88"
        assert res.action_taken == "blackhole"
        mock_audit.assert_called_once()
        db.commit.assert_called_once()
