# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Hito 20: Suite Corporativa de Gestión de Flota y Cumplimiento Normativo.

Cubre Sub-tareas 20.1 a 20.6 / specs/33:
- 20.1: Config Drift & Auto-Revert a Golden Templates
- 20.2: Orquestador SD-WAN WireGuard Hub & Spoke y Failover Multi-WAN
- 20.3: Auditoría Automatizada CIS Benchmark y Auto-Hardening
- 20.4: Conmutación Segura, DHCP Snooping y Mitigación de Rogue DHCP
- 20.5: Telemetría de SLA en Tiempo Real y Exportación de Informes
- 20.6: Gestión Centralizada de Wi-Fi CAPsMAN / WiFiWave2
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.v1.compliance import (
    auto_harden_router,
    check_config_drift,
    create_golden_template,
    list_golden_templates,
    revert_config_drift,
    run_cis_audit,
)
from src.api.v1.sdwan import (
    configure_multi_wan_failover,
    get_sdwan_topology,
    provision_spoke_tunnel,
)
from src.api.v1.sla import (
    export_sla_report,
    get_sla_metrics,
    run_sla_probe,
)
from src.api.v1.switching import (
    enable_dhcp_snooping,
    get_dhcp_snooping_state,
    isolate_rogue_port,
    list_rogue_dhcp_alerts,
)
from src.api.v1.wifi import (
    create_capsman_ssid,
    get_capsman_overview,
    list_capsman_ssids,
    list_wifi_clients,
)
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterNetworkRoleEnum
from src.models.operations import GoldenConfigTemplate, SdwanSpokeTunnel, SlaProbeMetric
from src.schemas.enterprise import (
    CisAutoHardenRequest,
    ConfigDriftRevertRequest,
    DhcpSnoopingEnableRequest,
    GoldenTemplateCreateRequest,
    RogueDhcpIsolatePortRequest,
    SdwanMultiWanFailoverRequest,
    SdwanProvisionSpokeRequest,
    SlaProbeRunRequest,
    WifiSsidProfile,
)


class MockDbResult:
    def __init__(self, items: list[object] | None = None) -> None:
        self._items = items or []

    def scalar_one_or_none(self) -> object | None:
        return self._items[0] if self._items else None

    def scalars(self) -> "MockDbResult":
        return self

    def all(self) -> list[object]:
        return self._items


@pytest.fixture
def sample_tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_claims(sample_tenant_id: uuid.UUID) -> dict[str, str]:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(sample_tenant_id),
        "username": "admin_audit",
        "rol": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    }


@pytest.fixture
def mock_request() -> MagicMock:
    req = MagicMock()
    req.client.host = "192.168.1.100"
    req.headers = {"user-agent": "RoSGrid-QA-Browser/1.0"}
    return req


# ============================================================================
# Sub-tarea 20.1 & 20.3: Config Drift, Golden Templates & CIS Benchmark
# ============================================================================


@pytest.mark.asyncio
async def test_golden_templates_listing_and_creation(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str]
) -> None:
    db = AsyncMock()
    # List when empty returns canonical default baselines
    db.execute.return_value = MockDbResult([])
    defaults = await list_golden_templates(db=db, claims=sample_claims)
    assert len(defaults) == 4
    assert any(t.network_role == "BRANCH" for t in defaults)

    # Creation of customized template
    payload = GoldenTemplateCreateRequest(
        name="Baseline-Core-Strict",
        network_role="CORE",
        baseline_rsc_content="/ip service set telnet disabled=yes\n/system ntp client set enabled=yes",
        enforce_strict_firewall=True,
        enforce_ntp_dns=True,
    )
    res = await create_golden_template(payload=payload, db=db, claims=sample_claims)
    assert res.name == "Baseline-Core-Strict"
    assert res.network_role == "CORE"
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_config_drift_identifies_unauthorized_changes(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str]
) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="Edge-Router-01",
        network_role=RouterNetworkRoleEnum.EDGE_BGP,
        api_base_url="https://10.0.0.1:443",
    )
    tpl = GoldenConfigTemplate(
        id=uuid.uuid4(),
        tenant_id=sample_tenant_id,
        name="Baseline-EDGE-Default",
        network_role="EDGE",
        baseline_rsc_content="/ip service set telnet disabled=yes\n/ip service set ftp disabled=yes",
    )

    db.execute.side_effect = [
        MockDbResult([mock_router]),
        MockDbResult([tpl]),
    ]

    mock_client = AsyncMock()
    # Simulate active config with unauthorized telnet enabled
    mock_client.request.return_value = {
        "script": "/ip service set telnet disabled=no\n/ip service set ftp disabled=yes\n/ip firewall filter add chain=input action=accept"
    }

    with patch("src.api.v1.compliance.get_router_and_client", return_value=(mock_router, mock_client)):
        res = await check_config_drift(router_id=router_id, db=db, claims=sample_claims)
        assert res.drift_detected is True
        assert res.router_name == "Edge-Router-01"
        assert res.total_drift_lines > 0


@pytest.mark.asyncio
async def test_revert_config_drift_executes_safemode_and_worm_audit(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str], mock_request: MagicMock
) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="Branch-Router-01",
        network_role=RouterNetworkRoleEnum.CORPORATE_CPE,
        api_base_url="https://10.0.0.2:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    mock_client = AsyncMock()
    mock_audit_entry = MagicMock()
    mock_audit_entry.id = uuid.uuid4()

    with (
        patch("src.api.v1.compliance.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.compliance.execute_safe_mutation", AsyncMock(return_value={"applied": 5})) as mock_safe,
        patch("src.api.v1.compliance.write_audit_log", AsyncMock(return_value=mock_audit_entry)) as mock_audit,
    ):
        payload = ConfigDriftRevertRequest(router_id=router_id)
        res = await revert_config_drift(payload=payload, request=mock_request, db=db, claims=sample_claims)
        assert res.status == "REVERTED_SUCCESSFULLY"
        assert res.executed_safemode is True
        mock_safe.assert_called_once()
        mock_audit.assert_called_once()


@pytest.mark.asyncio
async def test_audit_router_cis_benchmark_score_and_auto_hardening(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str], mock_request: MagicMock
) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="Core-Switch-01",
        network_role=RouterNetworkRoleEnum.CORE,
        api_base_url="https://10.0.0.3:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    mock_client = AsyncMock()
    mock_client.get.return_value = [
        {"name": "telnet", "disabled": True},
        {"name": "ftp", "disabled": True},
        {"name": "www", "disabled": True},
        {"name": "api", "disabled": True},
    ]

    with patch("src.api.v1.compliance.get_router_and_client", return_value=(mock_router, mock_client)):
        audit_res = await run_cis_audit(router_id=router_id, db=db, claims=sample_claims)
        assert audit_res.router_name == "Core-Switch-01"
        assert audit_res.security_score >= 60
        assert len(audit_res.directives) == 10

    # Auto-Hardening
    mock_audit_entry = MagicMock()
    mock_audit_entry.id = uuid.uuid4()
    with (
        patch("src.api.v1.compliance.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.compliance.execute_safe_mutation", AsyncMock(return_value={"status": "ok"})) as mock_safe,
        patch("src.api.v1.compliance.write_audit_log", AsyncMock(return_value=mock_audit_entry)) as mock_audit,
    ):
        harden_payload = CisAutoHardenRequest(router_id=router_id, directive_codes_to_apply=["CIS-1.1", "CIS-1.3"])
        harden_res = await auto_harden_router(
            router_id=router_id, payload=harden_payload, request=mock_request, db=db, claims=sample_claims
        )
        assert harden_res.new_security_score == 100
        assert harden_res.executed_under_safemode is True
        mock_safe.assert_called_once()
        mock_audit.assert_called_once()


# ============================================================================
# Sub-tarea 20.2: SD-WAN WireGuard Hub & Spoke & Failover
# ============================================================================


@pytest.mark.asyncio
async def test_provision_sdwan_spoke_and_topology(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str], mock_request: MagicMock
) -> None:
    db = AsyncMock()
    hub_id = uuid.uuid4()
    spoke_id = uuid.uuid4()

    hub_router = Router(
        id=hub_id,
        tenant_id=sample_tenant_id,
        display_name="Hub-Central",
        network_role=RouterNetworkRoleEnum.CORE,
        api_base_url="https://200.1.1.1:443",
    )
    spoke_router = Router(
        id=spoke_id,
        tenant_id=sample_tenant_id,
        display_name="Spoke-Sucursal-Maracaibo",
        network_role=RouterNetworkRoleEnum.CORPORATE_CPE,
        api_base_url="https://190.2.2.2:443",
    )

    db.execute.side_effect = [
        MockDbResult([hub_router]),
        MockDbResult([spoke_router]),
        MockDbResult([]),  # No existing tunnel
    ]

    mock_audit_entry = MagicMock()
    mock_audit_entry.id = uuid.uuid4()

    with patch("src.api.v1.sdwan.write_audit_log", AsyncMock(return_value=mock_audit_entry)):
        req = SdwanProvisionSpokeRequest(
            hub_router_id=hub_id,
            spoke_router_id=spoke_id,
            spoke_name="Maracaibo-Branch",
            routing_protocol="BGP",
            multi_wan_failover_enabled=True,
        )
        tunnel_res = await provision_spoke_tunnel(payload=req, request=mock_request, db=db, claims=sample_claims)
        assert tunnel_res.spoke_name == "Maracaibo-Branch"
        assert tunnel_res.status == "ACTIVE"
        assert tunnel_res.routing_protocol == "BGP"
        db.add.assert_called_once()

    # Topology query
    tunnel_obj = SdwanSpokeTunnel(
        id=uuid.uuid4(),
        tenant_id=sample_tenant_id,
        hub_router_id=hub_id,
        spoke_router_id=spoke_id,
        spoke_name="Maracaibo-Branch",
        interface_name="wg-sdwan0",
        allocated_subnet="10.250.0.0/31",
        hub_endpoint="200.1.1.1:51820",
        spoke_public_key="k3YMockWireGuardPublicKey==",
        routing_protocol="BGP",
        multi_wan_failover_enabled=True,
        status="ACTIVE",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.execute.side_effect = [
        MockDbResult([tunnel_obj]),
        MockDbResult([hub_router, spoke_router]),
    ]
    topo = await get_sdwan_topology(tenant_id=sample_tenant_id, db=db, claims=sample_claims)
    assert topo.total_spokes == 1
    assert len(topo.tunnels) == 1


@pytest.mark.asyncio
async def test_deploy_multi_wan_failover_policy(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str], mock_request: MagicMock
) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="DualWAN-Branch",
        network_role=RouterNetworkRoleEnum.CORPORATE_CPE,
        api_base_url="https://10.0.0.10:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    mock_client = AsyncMock()
    with (
        patch("src.api.v1.sdwan.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.sdwan.execute_safe_mutation", AsyncMock(return_value={"status": "deployed"})),
        patch("src.api.v1.sdwan.write_audit_log", AsyncMock()),
    ):
        failover_req = SdwanMultiWanFailoverRequest(
            router_id=router_id,
            primary_wan_interface="ether1-fiber",
            backup_wan_interface="lte1",
            check_host="1.1.1.1",
            failover_threshold_ms=80.0,
        )
        res = await configure_multi_wan_failover(
            payload=failover_req, request=mock_request, db=db, claims=sample_claims
        )
        assert res.failover_policy_deployed is True
        assert res.deployed_under_safemode is True


# ============================================================================
# Sub-tarea 20.4: Switching & Rogue DHCP Isolation
# ============================================================================


@pytest.mark.asyncio
async def test_dhcp_snooping_state_and_enable(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str], mock_request: MagicMock
) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="CRS328-Switch",
        network_role=RouterNetworkRoleEnum.DISTRIBUTION_SWITCH,
        api_base_url="https://10.0.0.20:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        [{"name": "bridge1", "dhcp-snooping": "true"}],
        [{"bridge": "bridge1", "interface": "sfp-sfpplus1", "trusted": "true"}],
    ]

    with patch("src.api.v1.switching.get_router_and_client", return_value=(mock_router, mock_client)):
        state_res = await get_dhcp_snooping_state(router_id=router_id, db=db, claims=sample_claims)
        assert len(state_res) == 1
        assert state_res[0].bridge_name == "bridge1"
        assert state_res[0].dhcp_snooping_enabled is True
        assert "sfp-sfpplus1" in state_res[0].trusted_ports

    # Enable DHCP Snooping
    with (
        patch("src.api.v1.switching.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.switching.execute_safe_mutation", AsyncMock(return_value={"status": "ok"})),
        patch("src.api.v1.switching.write_audit_log", AsyncMock()),
    ):
        enable_req = DhcpSnoopingEnableRequest(
            router_id=router_id,
            bridge_name="bridge1",
            trusted_ports=["sfp-sfpplus1", "ether1"],
        )
        en_res = await enable_dhcp_snooping(payload=enable_req, request=mock_request, db=db, claims=sample_claims)
        assert en_res.dhcp_snooping_enabled is True
        assert "ether1" in en_res.trusted_ports


@pytest.mark.asyncio
async def test_rogue_dhcp_detection_and_port_isolation(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, str], mock_request: MagicMock
) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="Edge-Access-01",
        network_role=RouterNetworkRoleEnum.CORPORATE_CPE,
        api_base_url="https://10.0.0.30:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    alerts = await list_rogue_dhcp_alerts(router_id=router_id, db=db, claims=sample_claims)
    assert len(alerts) >= 1
    assert alerts[0].rogue_server_mac == "B8:69:F4:11:22:33"

    # Isolate port
    mock_client = AsyncMock()
    mock_audit = MagicMock()
    mock_audit.id = uuid.uuid4()

    with (
        patch("src.api.v1.switching.get_router_and_client", return_value=(mock_router, mock_client)),
        patch("src.api.v1.switching.execute_safe_mutation", AsyncMock(return_value={"isolated": True})),
        patch("src.api.v1.switching.write_audit_log", AsyncMock(return_value=mock_audit)),
    ):
        iso_req = RogueDhcpIsolatePortRequest(
            router_id=router_id,
            interface_name="ether4",
            reason="Unauthorized DHCP server offering 192.168.1.0/24 leases",
        )
        iso_res = await isolate_rogue_port(payload=iso_req, request=mock_request, db=db, claims=sample_claims)
        assert iso_res.isolated is True
        assert iso_res.interface_name == "ether4"
        assert iso_res.executed_under_safemode is True


# ============================================================================
# Sub-tarea 20.5: SLA Tracker & Exportación de Reportes
# ============================================================================


@pytest.mark.asyncio
async def test_sla_metrics_query_and_probe_trigger(sample_tenant_id: uuid.UUID, sample_claims: dict[str, str]) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="SLA-Core-Gateway",
        network_role=RouterNetworkRoleEnum.CORE,
        api_base_url="https://10.0.0.40:443",
    )
    mock_metric = SlaProbeMetric(
        id=uuid.uuid4(),
        tenant_id=sample_tenant_id,
        router_id=router_id,
        target_host="8.8.8.8",
        target_name="Google-DNS",
        uptime_percent=99.98,
        avg_latency_ms=12.4,
        p95_latency_ms=18.5,
        p99_latency_ms=25.0,
        jitter_ms=1.8,
        packet_loss_pct=0.0,
        sla_threshold_ms=50.0,
        compliance_status="COMPLIANT",
        recorded_at=datetime.now(UTC),
    )
    db.execute.side_effect = [
        MockDbResult([mock_router]),
        MockDbResult([mock_metric]),
        MockDbResult([mock_router]),  # for run_sla_probe
    ]

    metrics = await get_sla_metrics(router_id=router_id, limit=20, db=db, claims=sample_claims)
    assert len(metrics) == 1
    assert metrics[0].target_host == "8.8.8.8"
    assert metrics[0].compliance_status == "COMPLIANT"

    # Immediate Probe
    mock_client = AsyncMock()
    mock_client.post.return_value = [
        {"time": "10ms"},
        {"time": "12ms"},
        {"time": "14ms"},
        {"time": "15ms"},
        {"time": "16ms"},
    ]
    with patch("src.api.v1.sla.get_router_and_client", return_value=(mock_router, mock_client)):
        probe_req = SlaProbeRunRequest(
            router_id=router_id,
            target_host="8.8.8.8",
            target_name="Google-DNS",
            sla_threshold_ms=50.0,
            count=5,
        )
        probe_res = await run_sla_probe(payload=probe_req, db=db, claims=sample_claims)
        assert probe_res.target_host == "8.8.8.8"
        assert probe_res.avg_latency_ms > 0
        assert probe_res.compliance_status == "COMPLIANT"
        db.add.assert_called_once()


@pytest.mark.asyncio
async def test_export_sla_compliance_report(sample_tenant_id: uuid.UUID, sample_claims: dict[str, str]) -> None:
    db = AsyncMock()
    mock_metric = SlaProbeMetric(
        id=uuid.uuid4(),
        tenant_id=sample_tenant_id,
        router_id=uuid.uuid4(),
        target_host="1.1.1.1",
        target_name="Cloudflare",
        uptime_percent=99.99,
        avg_latency_ms=8.5,
        p95_latency_ms=12.0,
        p99_latency_ms=18.0,
        jitter_ms=0.9,
        packet_loss_pct=0.0,
        sla_threshold_ms=40.0,
        compliance_status="COMPLIANT",
        recorded_at=datetime.now(UTC),
    )
    db.execute.return_value = MockDbResult([mock_metric])

    report = await export_sla_report(db=db, claims=sample_claims)
    assert len(report.metrics) == 1
    assert report.global_uptime_percent > 99.0
    assert report.total_targets_monitored >= 1


# ============================================================================
# Sub-tarea 20.6: Wi-Fi CAPsMAN / WiFiWave2
# ============================================================================


@pytest.mark.asyncio
async def test_capsman_overview_ssids_and_clients(sample_tenant_id: uuid.UUID, sample_claims: dict[str, str]) -> None:
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="CAPsMAN-Controller",
        network_role=RouterNetworkRoleEnum.CORPORATE_CPE,
        api_base_url="https://10.0.0.50:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        [{"name": "cap1"}, {"name": "cap2"}],
        [{"mac-address": "A1:B2:C3:D4:E5:F6"}, {"mac-address": "11:22:33:44:55:66"}],
    ]

    with patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, mock_client)):
        overview = await get_capsman_overview(router_id=router_id, db=db, claims=sample_claims)
        assert overview.capsman_running is True
        assert overview.managed_aps_count == 2
        assert overview.connected_clients_count == 2

    # SSIDs
    ssids = await list_capsman_ssids(router_id=router_id, db=db, claims=sample_claims)
    assert len(ssids) == 3
    assert any(s.ssid == "CORP-SECURE-WIFI" for s in ssids)
    assert any(s.security_type == "WPA3-Enterprise 802.1X" for s in ssids)

    # Create SSID
    create_req = WifiSsidProfile(
        id="mock-ssid-1",
        name="Portal-Invitados",
        ssid="RoSGrid-Guest-Portal",
        security_type="WPA2-PSK",
        vlan_id=200,
        client_isolation=True,
        rate_limit_profile="20M/5M",
    )
    new_ssid = await create_capsman_ssid(router_id=router_id, payload=create_req, db=db, claims=sample_claims)
    assert new_ssid.ssid == "RoSGrid-Guest-Portal"
    assert new_ssid.vlan_id == 200

    # Clients
    clients = await list_wifi_clients(router_id=router_id, db=db, claims=sample_claims)
    assert len(clients) >= 2
    assert clients[0].signal_rssi_dbm < 0
    assert clients[0].fast_roaming_supported is True
