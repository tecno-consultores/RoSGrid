# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Diagnóstico 360°, BGP Looking Glass e IPFIX Mitigación (Hito 18)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.v1.bgp_looking_glass import (
    _parse_advertised_item,
    _parse_communities,
    _parse_route_item,
    get_looking_glass_advertised,
    get_looking_glass_route,
)
from src.api.v1.diagnostics_360 import (
    _calculate_ping_stats,
    _classify_disconnect_reason,
    _classify_log_message,
    _evaluate_overall_status,
    _parse_rtt_ms,
    _parse_torch_flows,
    _parse_torch_rate,
    run_endpoint_360_diagnostics,
)
from src.api.v1.traffic_flow import (
    _analyze_connections,
    _extract_ip_from_address,
    detect_traffic_anomalies,
    mitigate_traffic_anomaly,
)
from src.models.core import SystemRoleEnum
from src.schemas.diagnostics_360 import Endpoint360Request
from src.schemas.traffic_flow import TrafficMitigationRequest

# ============================================================================
# 1. DIAGNOSTICS 360 HELPERS & PARSING
# ============================================================================


def test_parse_rtt_ms_various_formats() -> None:
    assert _parse_rtt_ms(None) is None
    assert _parse_rtt_ms("") is None
    assert _parse_rtt_ms(15) == 15.0
    assert _parse_rtt_ms(24.5) == 24.5
    assert _parse_rtt_ms("18.2ms") == 18.2
    assert _parse_rtt_ms("0.025s") == 25.0
    assert _parse_rtt_ms("invalid") is None


def test_calculate_ping_stats_success_and_loss() -> None:
    raw_success = [
        {"status": "ok", "time": "10ms"},
        {"status": "ok", "time": "12ms"},
        {"status": "ok", "time": "14ms"},
    ]
    stats = _calculate_ping_stats(64, 3, raw_success, df_bit=False)
    assert stats.sent == 3
    assert stats.received == 3
    assert stats.packet_loss_pct == 0.0
    assert stats.min_rtt_ms == 10.0
    assert stats.avg_rtt_ms == 12.0
    assert stats.max_rtt_ms == 14.0
    assert stats.jitter_ms == 2.0
    assert stats.df_bit is False

    raw_partial = [
        {"status": "ok", "time": "20ms"},
        {"status": "timeout"},
    ]
    stats_p = _calculate_ping_stats(512, 3, raw_partial, df_bit=False)
    assert stats_p.sent == 3
    assert stats_p.received == 1
    assert stats_p.packet_loss_pct == 66.67
    assert stats_p.min_rtt_ms == 20.0
    assert stats_p.jitter_ms == 0.0

    stats_empty = _calculate_ping_stats(1472, 3, [], df_bit=True)
    assert stats_empty.received == 0
    assert stats_empty.packet_loss_pct == 100.0
    assert stats_empty.min_rtt_ms is None
    assert stats_empty.jitter_ms is None
    assert stats_empty.df_bit is True


def test_classify_log_message_and_reasons() -> None:
    assert _classify_log_message("user requested disconnect") == "user request"
    assert _classify_log_message("peer is not responding to echo") == "peer is not responding"
    assert _classify_log_message("ether1 link down") == "link down"
    assert _classify_log_message("authentication failed for subscriber") == "authentication failed"
    assert _classify_log_message("unrelated dhcp packet") is None


def test_classify_disconnect_reason_with_logs() -> None:
    raw_logs = [
        {"time": "10:00:00", "topics": "system,info", "message": "Router booted"},
        {"time": "10:05:00", "topics": "ppp,info", "message": "PPPoE user 10.10.1.50 disconnected: user request"},
        {"time": "10:10:00", "topics": "interface,warning", "message": "ether2 link down for ZTE123"},
    ]
    analysis = _classify_disconnect_reason(raw_logs, target_ip="10.10.1.50", device_serial="ZTE123")
    assert analysis.detected_reason == "link down"
    assert analysis.last_disconnect_time == "10:10:00"
    assert len(analysis.matched_logs) == 2


def test_parse_torch_rate_and_flows() -> None:
    assert _parse_torch_rate(None) == 0.0
    assert _parse_torch_rate(5000) == 5.0
    assert _parse_torch_rate("250kbps") == 250.0
    assert _parse_torch_rate("2.5mbps") == 2500.0
    assert _parse_torch_rate("1000bps") == 1.0
    assert _parse_torch_rate("garbage") == 0.0

    raw_torch = [
        {"protocol": "tcp", "dst-port": "443", "tx": "50000", "rx": "200000", "src-address": "10.0.0.1"},
        {"protocol": "udp", "dst-port": "53", "tx": "1000", "rx": "2000", "src-address": "10.0.0.1"},
        {"protocol": "icmp", "tx": "500", "rx": "500", "src-address": "10.0.0.1"},
    ]
    flows = _parse_torch_flows(raw_torch)
    assert len(flows) == 3
    assert flows[0].protocol == "tcp"
    assert flows[0].port == 443
    assert flows[0].tx_rate_kbps == 50.0
    assert flows[0].rx_rate_kbps == 200.0


def test_evaluate_overall_status() -> None:
    opt_64 = _calculate_ping_stats(64, 3, [{"status": "ok", "time": "10ms"}] * 3)
    opt_512 = _calculate_ping_stats(512, 3, [{"status": "ok", "time": "12ms"}] * 3)
    opt_1472 = _calculate_ping_stats(1472, 3, [{"status": "ok", "time": "15ms"}] * 3)

    assert _evaluate_overall_status(opt_64, opt_512, opt_1472, dispersion=False) == "OPTIMAL"
    assert _evaluate_overall_status(opt_64, opt_512, opt_1472, dispersion=True) == "DEGRADED"

    loss_1472 = _calculate_ping_stats(1472, 3, [])
    assert _evaluate_overall_status(opt_64, opt_512, loss_1472, dispersion=False) == "DEGRADED"

    down_64 = _calculate_ping_stats(64, 3, [])
    down_512 = _calculate_ping_stats(512, 3, [])
    assert _evaluate_overall_status(down_64, down_512, loss_1472, dispersion=False) == "DOWN"


# ============================================================================
# 2. BGP LOOKING GLASS HELPERS & PARSING
# ============================================================================


def test_parse_communities() -> None:
    assert _parse_communities(None) == []
    assert _parse_communities(["65001:100", "65001:200"]) == ["65001:100", "65001:200"]
    assert _parse_communities("65001:100, 65001:200") == ["65001:100", "65001:200"]
    assert _parse_communities("65001:300") == ["65001:300"]


def test_parse_route_item_and_advertised_item() -> None:
    raw_route = {
        "dst": "190.200.10.0/24",
        "gateway": "186.10.20.1",
        "immediate-gw": "186.10.20.1%ether1",
        "as-path": "65001 13335",
        "communities": "65001:100, 65001:500",
        "scope": "30",
        "active": "true",
        "uptime": "5d12h",
    }
    route = _parse_route_item(raw_route)
    assert route.prefix == "190.200.10.0/24"
    assert route.gateway == "186.10.20.1"
    assert route.as_path == "65001 13335"
    assert len(route.communities) == 2
    assert route.scope == 30
    assert route.active is True

    raw_adv = {
        "peer": "ISP-Uplink-1",
        "dst": "190.200.10.0/24",
        "nexthop": "186.10.20.2",
        "as-path": "65000",
        "origin": "igp",
        "communities": ["65000:10"],
    }
    adv = _parse_advertised_item("ISP-Uplink-1", raw_adv)
    assert adv.peer == "ISP-Uplink-1"
    assert adv.prefix == "190.200.10.0/24"
    assert adv.nexthop == "186.10.20.2"
    assert adv.origin == "igp"


# ============================================================================
# 3. TRAFFIC FLOW ANOMALIES & MITIGATION HELPERS
# ============================================================================


def test_extract_ip_from_address() -> None:
    assert _extract_ip_from_address("192.168.1.50:54321") == "192.168.1.50"
    assert _extract_ip_from_address("10.0.0.1") == "10.0.0.1"
    assert _extract_ip_from_address("  172.16.0.5:80  ") == "172.16.0.5"


def test_analyze_connections() -> None:
    raw_conns = []
    # Host A: 600 connections (over 500 threshold), low packet rate (pps = 600 < 1000)
    for _ in range(600):
        raw_conns.append({"src-address": "192.168.88.10:1234", "protocol": "tcp", "orig-packets": 2})
    # Host B: 10 connections (normal)
    for _ in range(10):
        raw_conns.append({"src-address": "192.168.88.20:4321", "protocol": "udp", "orig-packets": 1})

    anomalies = _analyze_connections(raw_conns, threshold_pps=1000, threshold_conns=500)
    assert len(anomalies) == 1
    assert anomalies[0].ip_address == "192.168.88.10"
    assert anomalies[0].connection_count == 600
    assert anomalies[0].anomaly_type == "HIGH_CONNECTION_COUNT"
    assert anomalies[0].severity == "HIGH"


# ============================================================================
# 4. ENDPOINT INTEGRATION UNIT TESTS (WITH MOCKED DB & CLIENT)
# ============================================================================


@pytest.mark.asyncio
async def test_run_endpoint_360_diagnostics_endpoint() -> None:
    router_id = uuid.uuid4()
    claims = {"tid": str(uuid.uuid4()), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.SUPPORT_L2.value}
    db = AsyncMock()

    mock_client = AsyncMock()
    mock_client.post.side_effect = [
        [{"status": "ok", "time": "12ms"}] * 3,  # 64B
        [{"status": "ok", "time": "14ms"}] * 3,  # 512B
        [{"status": "ok", "time": "16ms"}] * 3,  # 1472B
        [{"protocol": "tcp", "dst-port": "80", "tx": "10000", "rx": "40000"}],  # Torch
    ]
    mock_client.get.return_value = [
        {"time": "11:00:00", "topics": "ppp,info", "message": "PPPoE 10.10.1.50 disconnected: user request"}
    ]

    mock_router_obj = MagicMock()
    mock_router_obj.id = router_id

    with patch("src.api.v1.diagnostics_360.get_router_and_client", return_value=(mock_router_obj, mock_client)):
        req = Endpoint360Request(
            router_id=router_id,
            target_ip="10.10.1.50",
            device_serial="ZTE12345",
            interface="ether1",
        )
        res = await run_endpoint_360_diagnostics(req, claims=claims, db=db)
        assert res.router_id == router_id
        assert res.target_ip == "10.10.1.50"
        assert res.overall_status == "OPTIMAL"
        assert res.multi_mtu.ping_64.received == 3
        assert res.multi_mtu.ping_1472.df_bit is True
        assert res.disconnect_analysis.detected_reason == "user request"
        assert len(res.torch_top_flows) == 1


@pytest.mark.asyncio
async def test_get_looking_glass_route_and_advertised() -> None:
    router_id = uuid.uuid4()
    claims = {"tid": str(uuid.uuid4()), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.SUPPORT_L1.value}
    db = AsyncMock()

    mock_client = AsyncMock()
    mock_router_obj = MagicMock()
    mock_router_obj.id = router_id

    routes_data = [
        {"dst": "1.1.1.0/24", "gateway": "10.0.0.1", "as-path": "13335", "active": True},
        {"dst": "8.8.8.0/24", "gateway": "10.0.0.2", "as-path": "15169", "active": True},
    ]

    with (
        patch("src.api.v1.bgp_looking_glass.get_router_and_client", return_value=(mock_router_obj, mock_client)),
        patch("src.api.v1.bgp_looking_glass.cached_mikrotik_get", return_value=routes_data),
    ):
        res = await get_looking_glass_route(
            router_id=router_id,
            prefix="1.1.1.0/24",
            refresh=True,
            claims=claims,
            db=db,
        )
        assert res.router_id == router_id
        assert res.prefix == "1.1.1.0/24"
        assert res.total_routes == 1
        assert res.routes[0].gateway == "10.0.0.1"

    adv_data = [
        {"peer": "Transit-A", "dst": "190.200.0.0/22", "nexthop": "10.0.0.5"},
    ]
    with (
        patch("src.api.v1.bgp_looking_glass.get_router_and_client", return_value=(mock_router_obj, mock_client)),
        patch("src.api.v1.bgp_looking_glass.cached_mikrotik_get", return_value=adv_data),
    ):
        adv_res = await get_looking_glass_advertised(
            router_id=router_id,
            peer="Transit-A",
            refresh=False,
            claims=claims,
            db=db,
        )
        assert adv_res.router_id == router_id
        assert adv_res.total_advertised == 1
        assert adv_res.advertisements[0].nexthop == "10.0.0.5"


@pytest.mark.asyncio
async def test_detect_traffic_anomalies_and_mitigate() -> None:
    router_id = uuid.uuid4()
    claims = {
        "tid": str(uuid.uuid4()),
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.SUPPORT_L2.value,
    }
    db = AsyncMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {"src-address": "192.168.1.100:1234", "protocol": "tcp", "orig-packets": 20} for _ in range(600)
    ]
    mock_router_obj = MagicMock()
    mock_router_obj.id = router_id
    mock_router_obj.display_name = "Core-Edge-01"

    with patch("src.api.v1.traffic_flow.get_router_and_client", return_value=(mock_router_obj, mock_client)):
        res = await detect_traffic_anomalies(
            router_id=router_id,
            threshold_pps=500,
            threshold_conns=500,
            claims=claims,
            db=db,
        )
        assert res.anomalies_detected == 1
        assert res.items[0].ip_address == "192.168.1.100"

    # Test Mitigate FastDrop
    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.99"
    mock_request.headers.get.return_value = "Pytest/1.0"

    with (
        patch("src.api.v1.traffic_flow.get_router_and_client", return_value=(mock_router_obj, mock_client)),
        patch("src.api.v1.traffic_flow.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.traffic_flow.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        mit_req = TrafficMitigationRequest(
            router_id=router_id,
            target_ip="192.168.1.100",
            action="fast_drop",
            comment="FastDrop SYN Flood",
            duration_seconds=3600,
        )
        mit_res = await mitigate_traffic_anomaly(
            payload=mit_req,
            request=mock_request,
            claims=claims,
            db=db,
        )
        assert mit_res.status == "MITIGATED"
        assert mit_res.action_taken == "fast_drop"
        assert mit_res.safemode_applied is True
        assert mock_audit.called

    # Test Mitigate Blackhole
    with (
        patch("src.api.v1.traffic_flow.get_router_and_client", return_value=(mock_router_obj, mock_client)),
        patch("src.api.v1.traffic_flow.execute_safe_mutation", return_value={"ret": "*2"}),
        patch("src.api.v1.traffic_flow.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        bh_req = TrafficMitigationRequest(
            router_id=router_id,
            target_ip="192.168.1.200",
            action="blackhole",
            comment="Blackhole Attack IP",
            duration_seconds=1800,
        )
        bh_res = await mitigate_traffic_anomaly(
            payload=bh_req,
            request=mock_request,
            claims=claims,
            db=db,
        )
        assert bh_res.status == "MITIGATED"
        assert bh_res.action_taken == "blackhole"
        assert mock_audit.called
