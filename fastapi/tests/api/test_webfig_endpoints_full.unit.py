# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite Completa de Pruebas Unitarias de Endpoints WebFig (Interfaces, IP, Firewall, Routing, PPP, Queues, System y L2)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import src.api.v1.webfig_common as api_wf_common
import src.api.v1.webfig_firewall as api_wf_firewall
import src.api.v1.webfig_interfaces as api_wf_interfaces
import src.api.v1.webfig_ip as api_wf_ip
import src.api.v1.webfig_layer2 as api_wf_l2
import src.api.v1.webfig_ppp as api_wf_ppp
import src.api.v1.webfig_queues as api_wf_queues
import src.api.v1.webfig_routing as api_wf_routing
import src.api.v1.webfig_system_tools as api_wf_systools
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterCredentialsVault
from src.schemas.webfig_firewall import (
    AddressListCreateRequest,
    BgpConnectionCreateRequest,
    BgpConnectionUpdateRequest,
    FirewallRuleCreateRequest,
    FirewallRuleMoveRequest,
    FirewallRuleUpdateRequest,
    RoutingFilterRuleCreateRequest,
    RoutingFilterRuleUpdateRequest,
    RoutingRuleCreateRequest,
    RoutingTableCreateRequest,
)
from src.schemas.webfig_l1_net import (
    BridgeCreateRequest,
    BridgePortCreateRequest,
    BridgeUpdateRequest,
    DhcpLeaseUpdateRequest,
    IpAddressCreateRequest,
    IpAddressUpdateRequest,
    IpArpCreateRequest,
    IpPoolCreateRequest,
    IpRouteCreateRequest,
    IpRouteUpdateRequest,
    IpServiceUpdateRequest,
    UpdateInterfaceRequest,
    VlanCreateRequest,
    VlanUpdateRequest,
    WireGuardCreateRequest,
    WireGuardPeerCreateRequest,
)
from src.schemas.webfig_layer2 import DynamicLayer2WriteRequest
from src.schemas.webfig_ops import (
    PppoeServerCreateRequest,
    PppProfileCreateRequest,
    PppProfileUpdateRequest,
    PppSecretCreateRequest,
    PppSecretUpdateRequest,
    QueueMoveRequest,
    QueueSimpleCreateRequest,
    QueueSimpleUpdateRequest,
    QueueTreeCreateRequest,
    QueueTreeUpdateRequest,
    RouterPingRequest,
    RouterTorchRequest,
    RouterTracerouteRequest,
    SystemIdentityUpdateRequest,
    SystemRebootRequest,
    SystemScriptCreateRequest,
    SystemUserCreateRequest,
    SystemUserUpdateRequest,
)


@pytest.fixture
def fake_client_and_router() -> tuple[Router, AsyncMock]:
    t_id = uuid.uuid4()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=t_id,
        display_name="Edge-Test",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
    )
    client = AsyncMock()
    client.get.return_value = [{"name": "ether1", ".id": "*1", "status": "link-ok"}]
    client.post.return_value = {"ret": "*1"}
    client.put.return_value = {"ret": "*1"}
    client.patch.return_value = {"ret": "*1"}
    client.delete.return_value = {}
    client.close = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return r, client


# ============================================================================
# WEBFIG INTERFACES ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_interfaces_endpoints(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_interfaces.cached_mikrotik_get", return_value=[{"name": "ether1"}]),
        patch("src.api.v1.webfig_interfaces.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_interfaces.get_redis_client", return_value=AsyncMock()),
    ):
        assert await api_wf_interfaces.list_interfaces(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "ether1"}
        ]
        assert await api_wf_interfaces.update_interface(
            r.id, "*1", UpdateInterfaceRequest(comment="test"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_interfaces.list_ethernet(r.id, refresh=False, claims=claims, db=db) == [{"name": "ether1"}]

        client.post.return_value = {"status": "complete", "name": "ether1"}
        cable_res = await api_wf_interfaces.cable_test(r.id, "*1", claims=claims, db=db)
        assert cable_res.interface_id == "*1"

        client.post.return_value = {"status": "link-ok", "name": "sfp-sfpplus1", "sfp-rx-power": "-12.5"}
        sfp_res = await api_wf_interfaces.sfp_monitor(r.id, "*1", claims=claims, db=db)
        assert sfp_res.optical_health == "OPTIMAL"

        assert await api_wf_interfaces.list_vlans(r.id, refresh=False, claims=claims, db=db) == [{"name": "ether1"}]
        assert await api_wf_interfaces.create_vlan(
            r.id, VlanCreateRequest(name="v10", vlan_id=10, interface="ether1"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_interfaces.update_vlan(
            r.id, "*1", VlanUpdateRequest(comment="vlan10"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_interfaces.delete_vlan(r.id, "*1", claims=claims, db=db) == {"ret": "*1"}

        assert await api_wf_interfaces.list_bridges(r.id, refresh=False, claims=claims, db=db) == [{"name": "ether1"}]
        assert await api_wf_interfaces.create_bridge(r.id, BridgeCreateRequest(name="br0"), claims=claims, db=db) == {
            "ret": "*1"
        }
        assert await api_wf_interfaces.update_bridge(
            r.id, "*1", BridgeUpdateRequest(comment="br0"), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_interfaces.list_bridge_ports(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "ether1"}
        ]
        assert await api_wf_interfaces.create_bridge_port(
            r.id, BridgePortCreateRequest(bridge="br0", interface="ether1"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_interfaces.list_bridge_vlans(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "ether1"}
        ]
        assert await api_wf_interfaces.list_bridge_hosts(r.id, claims=claims, db=db) == [{"name": "ether1"}]

        assert await api_wf_interfaces.list_wireguard(r.id, refresh=False, claims=claims, db=db) == [{"name": "ether1"}]
        assert await api_wf_interfaces.create_wireguard(
            r.id, WireGuardCreateRequest(name="wg0", listen_port=13231), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_interfaces.list_wireguard_peers(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "ether1"}
        ]
        wg_peer_req = WireGuardPeerCreateRequest(interface="wg0", public_key="a" * 32, allowed_address="10.0.0.2/32")
        assert await api_wf_interfaces.create_wireguard_peer(r.id, wg_peer_req, claims=claims, db=db) == {"ret": "*1"}
        assert await api_wf_interfaces.list_wifi_registrations(r.id, claims=claims, db=db) == [{"name": "ether1"}]


# ============================================================================
# WEBFIG IP ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_ip_endpoints(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.cached_mikrotik_get", return_value=[{"address": "10.0.0.1/24"}]),
        patch("src.api.v1.webfig_ip.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_ip.get_redis_client", return_value=AsyncMock()),
    ):
        assert await api_wf_ip.list_ip_addresses(r.id, refresh=False, claims=claims, db=db) == [
            {"address": "10.0.0.1/24"}
        ]
        assert await api_wf_ip.create_ip_address(
            r.id, IpAddressCreateRequest(address="192.168.1.1/24", interface="ether1"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ip.update_ip_address(
            r.id, "*1", IpAddressUpdateRequest(comment="test"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ip.delete_ip_address(r.id, "*1", claims=claims, db=db) == {"ret": "*1"}

        assert await api_wf_ip.list_routes(r.id, refresh=False, claims=claims, db=db) == [{"address": "10.0.0.1/24"}]
        assert await api_wf_ip.create_route(
            r.id, IpRouteCreateRequest(dst_address="0.0.0.0/0", gateway="192.168.1.254"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ip.update_route(r.id, "*1", IpRouteUpdateRequest(comment="rt"), claims=claims, db=db) == {
            "ret": "*1"
        }
        assert await api_wf_ip.delete_route(r.id, "*1", claims=claims, db=db) == {"ret": "*1"}

        assert await api_wf_ip.list_arp(r.id, refresh=False, claims=claims, db=db) == [{"address": "10.0.0.1/24"}]
        assert await api_wf_ip.create_arp(
            r.id,
            IpArpCreateRequest(address="192.168.1.50", mac_address="00:11:22:33:44:55", interface="ether1"),
            claims=claims,
            db=db,
        ) == {"ret": "*1"}
        assert await api_wf_ip.delete_arp(r.id, "*1", claims=claims, db=db) == {}

        assert await api_wf_ip.list_pools(r.id, refresh=False, claims=claims, db=db) == [{"address": "10.0.0.1/24"}]
        assert await api_wf_ip.create_pool(
            r.id, IpPoolCreateRequest(name="pool1", ranges="10.0.0.10-10.0.0.50"), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_ip.list_dhcp_leases(r.id, refresh=False, claims=claims, db=db) == [
            {"address": "10.0.0.1/24"}
        ]
        assert await api_wf_ip.make_dhcp_lease_static(r.id, "*1", claims=claims, db=db) == {"ret": "*1"}
        assert await api_wf_ip.update_dhcp_lease(
            r.id, "*1", DhcpLeaseUpdateRequest(comment="lease"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ip.delete_dhcp_lease(r.id, "*1", claims=claims, db=db) == {}

        client.get.return_value = {"servers": "8.8.8.8"}
        client.post.return_value = {"ret": "*1"}
        assert await api_wf_ip.get_dns_info(r.id, claims=claims, db=db) == {
            "config": {"servers": "8.8.8.8"},
            "static_records": [],
        }
        assert await api_wf_ip.flush_dns_cache(r.id, claims=claims, db=db) == {"ret": "*1"}

        assert await api_wf_ip.list_neighbors(r.id, refresh=False, claims=claims, db=db) == [{"address": "10.0.0.1/24"}]
        assert await api_wf_ip.list_services(r.id, refresh=False, claims=claims, db=db) == [{"address": "10.0.0.1/24"}]
        assert await api_wf_ip.update_service(r.id, "*1", IpServiceUpdateRequest(port=8443), claims=claims, db=db) == {
            "ret": "*1"
        }


# ============================================================================
# WEBFIG FIREWALL ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_firewall_endpoints(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    with (
        patch("src.api.v1.webfig_firewall.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_firewall.cached_mikrotik_get", return_value=[{"chain": "input"}]),
        patch("src.api.v1.webfig_firewall.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_firewall.get_redis_client", return_value=AsyncMock()),
    ):
        assert await api_wf_firewall.list_rules(r.id, "ip", "filter", refresh=False, claims=claims, db=db) == [
            {"chain": "input"}
        ]
        assert await api_wf_firewall.create_rule(
            r.id, "ip", "filter", FirewallRuleCreateRequest(chain="forward", action="accept"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_firewall.update_rule(
            r.id, "ip", "filter", "*1", FirewallRuleUpdateRequest(comment="fw"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_firewall.delete_rule(r.id, "ip", "filter", "*1", claims=claims, db=db) == {"ret": "*1"}
        assert await api_wf_firewall.move_rule(
            r.id, "ip", "filter", FirewallRuleMoveRequest(numbers="*1", destination="*2"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_firewall.reset_counters(r.id, "ip", "filter", claims=claims, db=db) == {"ret": "*1"}

        addr_lists = await api_wf_firewall.list_address_lists(
            r.id, "ip", None, None, refresh=False, claims=claims, db=db
        )
        assert addr_lists == [{"chain": "input"}]
        assert await api_wf_firewall.create_address_list(
            r.id, "ip", AddressListCreateRequest(list="blacklist", address="10.0.0.99"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_firewall.delete_address_list(r.id, "ip", "*1", claims=claims, db=db) == {"ret": "*1"}

        assert await api_wf_firewall.list_connections(r.id, claims=claims, db=db) == [{"chain": "input"}]
        assert await api_wf_firewall.delete_connection(r.id, "*1", claims=claims, db=db) == {}


# ============================================================================
# WEBFIG ROUTING ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_routing_endpoints(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    with (
        patch("src.api.v1.webfig_routing.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_routing.cached_mikrotik_get", return_value=[{"name": "table1"}]),
        patch("src.api.v1.webfig_routing.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_routing.get_redis_client", return_value=AsyncMock()),
    ):
        assert await api_wf_routing.list_tables(r.id, refresh=False, claims=claims, db=db) == [{"name": "table1"}]
        assert await api_wf_routing.create_table(
            r.id, RoutingTableCreateRequest(name="custom", fib=True), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_routing.list_rules(r.id, refresh=False, claims=claims, db=db) == [{"name": "table1"}]
        assert await api_wf_routing.create_rule(
            r.id, RoutingRuleCreateRequest(action="lookup", table="custom"), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_routing.list_bgp_templates(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "table1"}
        ]
        assert await api_wf_routing.list_bgp_connections(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "table1"}
        ]
        assert await api_wf_routing.create_bgp_connection(
            r.id,
            BgpConnectionCreateRequest(name="peer1", remote_address="10.0.0.2", remote_as=65002),
            claims=claims,
            db=db,
        ) == {"ret": "*1"}
        assert await api_wf_routing.update_bgp_connection(
            r.id, "*1", BgpConnectionUpdateRequest(remote_as=65003), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_routing.delete_bgp_connection(r.id, "*1", claims=claims, db=db) == {"ret": "*1"}

        client.get.return_value = [{"name": "peer1", "remote.as": "65002"}]
        assert await api_wf_routing.get_bgp_sessions(r.id, claims=claims, db=db) is not None
        assert await api_wf_routing.get_bgp_advertisements(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "table1"}
        ]

        assert await api_wf_routing.list_ospf_instances(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "table1"}
        ]
        assert await api_wf_routing.list_ospf_areas(r.id, refresh=False, claims=claims, db=db) == [{"name": "table1"}]
        assert await api_wf_routing.list_ospf_interface_templates(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "table1"}
        ]
        assert await api_wf_routing.list_ospf_neighbors(r.id, claims=claims, db=db) == [{"name": "table1"}]
        assert await api_wf_routing.list_bfd_sessions(r.id, claims=claims, db=db) == [{"name": "table1"}]

        assert await api_wf_routing.list_filter_rules(r.id, refresh=False, claims=claims, db=db) == [{"name": "table1"}]
        assert await api_wf_routing.create_filter_rule(
            r.id, RoutingFilterRuleCreateRequest(chain="bgp-in", rule="accept"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_routing.update_filter_rule(
            r.id, "*1", RoutingFilterRuleUpdateRequest(comment="bgp rule"), claims=claims, db=db
        ) == {"ret": "*1"}


# ============================================================================
# WEBFIG PPP & QUEUES ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_ppp_and_queues_endpoints(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    with (
        patch("src.api.v1.webfig_ppp.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ppp.cached_mikrotik_get", return_value=[{"name": "profile1"}]),
        patch("src.api.v1.webfig_ppp.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_ppp.get_redis_client", return_value=AsyncMock()),
    ):
        assert await api_wf_ppp.list_active_sessions(r.id, refresh=False, claims=claims, db=db) == [
            {"name": "profile1"}
        ]
        assert await api_wf_ppp.disconnect_active_session(r.id, "*1", claims=claims, db=db) == {}

        assert await api_wf_ppp.list_secrets(r.id, refresh=False, claims=claims, db=db) == [{"name": "profile1"}]
        assert await api_wf_ppp.create_secret(
            r.id, PppSecretCreateRequest(name="user1", password="pwd", service="pppoe"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ppp.update_secret(
            r.id, "*1", PppSecretUpdateRequest(comment="u1"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ppp.delete_secret(r.id, "*1", claims=claims, db=db) == {}

        assert await api_wf_ppp.list_profiles(r.id, refresh=False, claims=claims, db=db) == [{"name": "profile1"}]
        assert await api_wf_ppp.create_profile(r.id, PppProfileCreateRequest(name="p1"), claims=claims, db=db) == {
            "ret": "*1"
        }
        assert await api_wf_ppp.update_profile(
            r.id, "*1", PppProfileUpdateRequest(rate_limit="10M/10M"), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_ppp.list_pppoe_servers(r.id, refresh=False, claims=claims, db=db) == [{"name": "profile1"}]
        assert await api_wf_ppp.create_pppoe_server(
            r.id, PppoeServerCreateRequest(service_name="srv1", interface="ether1"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_ppp.list_ipsec_peers(r.id, claims=claims, db=db) == [{"name": "profile1"}]

    with (
        patch("src.api.v1.webfig_queues.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_queues.cached_mikrotik_get", return_value=[{"name": "q1"}]),
        patch("src.api.v1.webfig_queues.get_redis_client", return_value=AsyncMock()),
    ):
        assert await api_wf_queues.list_simple_queues(r.id, refresh=False, claims=claims, db=db) == [{"name": "q1"}]
        assert await api_wf_queues.create_simple_queue(
            r.id, QueueSimpleCreateRequest(name="sq1", target="10.0.0.10", max_limit="10M/10M"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_queues.update_simple_queue(
            r.id, "*1", QueueSimpleUpdateRequest(max_limit="10M/10M"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_queues.delete_simple_queue(r.id, "*1", claims=claims, db=db) == {}
        assert await api_wf_queues.move_simple_queue(
            r.id, QueueMoveRequest(numbers="*1", destination="*2"), claims=claims, db=db
        ) == {"ret": "*1"}

        assert await api_wf_queues.list_queue_trees(r.id, refresh=False, claims=claims, db=db) == [{"name": "q1"}]
        assert await api_wf_queues.create_queue_tree(
            r.id, QueueTreeCreateRequest(name="qt1", parent="global"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_queues.update_queue_tree(
            r.id, "*1", QueueTreeUpdateRequest(packet_mark="pm1"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_queues.delete_queue_tree(r.id, "*1", claims=claims, db=db) == {}
        assert await api_wf_queues.list_queue_types(r.id, refresh=False, claims=claims, db=db) == [{"name": "q1"}]


# ============================================================================
# WEBFIG SYSTEM, TOOLS & LAYER 2 ENDPOINTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_system_tools_and_l2(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    fake_req = MagicMock()
    fake_req.client.host = "127.0.0.1"
    fake_req.headers.get.return_value = "TestAgent"

    with (
        patch("src.api.v1.webfig_system_tools.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_system_tools.cached_mikrotik_get", return_value=[{"name": "admin"}]),
        patch("src.api.v1.webfig_system_tools.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_system_tools.write_audit_log", new_callable=AsyncMock),
        patch("src.api.v1.webfig_system_tools.get_redis_client", return_value=AsyncMock()),
    ):
        client.get.return_value = {"cpu-load": 10, "free-memory": 500000}
        assert await api_wf_systools.get_live_status(r.id, claims=claims, db=db) is not None
        assert await api_wf_systools.update_identity(
            r.id, SystemIdentityUpdateRequest(name="Edge-New"), claims=claims, db=db
        ) == {"ret": "*1"}

        client.get.return_value = [{"name": "admin", "group": "full"}]
        assert (await api_wf_systools.list_system_users(r.id, claims=claims, db=db))["users"] == [
            {"name": "admin", "group": "full"}
        ]
        assert await api_wf_systools.create_system_user(
            r.id, SystemUserCreateRequest(name="noc_user", group="read", password="pwd"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_systools.update_system_user(
            r.id, "*1", SystemUserUpdateRequest(comment="noc"), claims=claims, db=db
        ) == {"ret": "*1"}

        client.get.return_value = [{"name": "test_script"}]
        assert await api_wf_systools.list_scripts(r.id, claims=claims, db=db) == [{"name": "test_script"}]
        assert await api_wf_systools.create_script(
            r.id, SystemScriptCreateRequest(name="test_script", source=":put hello"), claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_systools.run_script(r.id, "*1", claims=claims, db=db) == {"ret": "*1"}

        client.get.return_value = [{"name": "sched1"}]
        assert await api_wf_systools.list_schedulers(r.id, claims=claims, db=db) == [{"name": "sched1"}]
        client.get.return_value = [{"name": "routeros"}]
        assert (await api_wf_systools.list_packages(r.id, claims=claims, db=db))["packages"] == [{"name": "routeros"}]
        reboot_res = await api_wf_systools.reboot_router(
            r.id, SystemRebootRequest(reason="Planned reboot"), fake_req, claims=claims, db=db
        )
        assert reboot_res == {"status": "REBOOT_INITIATED", "reason": "Planned reboot"}

        client.post.return_value = [{"received": 5}]
        ping_res = await api_wf_systools.run_ping(
            r.id, RouterPingRequest(address="8.8.8.8", count=5), claims=claims, db=db
        )
        assert ping_res.target == "8.8.8.8"
        assert ping_res.sent == 5
        assert await api_wf_systools.run_traceroute(
            r.id, RouterTracerouteRequest(address="8.8.8.8"), claims=claims, db=db
        ) == [{"received": 5}]
        assert await api_wf_systools.run_torch(r.id, RouterTorchRequest(interface="ether1"), claims=claims, db=db) == [
            {"received": 5}
        ]
        assert await api_wf_systools.get_router_logs(r.id, None, claims=claims, db=db) == [{"name": "admin"}]

    with (
        patch("src.api.v1.webfig_layer2.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_layer2.cached_mikrotik_get", return_value=[{"name": "mpls1"}]),
        patch("src.api.v1.webfig_layer2.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.webfig_layer2.write_audit_log", new_callable=AsyncMock),
        patch("src.api.v1.webfig_layer2.from_deps_redis", return_value=AsyncMock()),
    ):
        catalog = await api_wf_l2.get_catalog(r.id, False, claims=claims, db=db)
        assert catalog.router_id == r.id

        client.get.return_value = [{"name": "mpls1", ".id": "*1"}]
        res = await api_wf_l2.get_resource(r.id, "interface/vpls", False, claims=claims, db=db)
        assert res.ros_path == "interface/vpls"

        write_req = DynamicLayer2WriteRequest(attributes={"name": "vpls2"}, enable_safemode=True)
        assert await api_wf_l2.create_resource(r.id, "interface/vpls", write_req, fake_req, claims=claims, db=db) == {
            "ret": "*1"
        }
        assert await api_wf_l2.update_resource(
            r.id, "interface/vpls", "*1", write_req, fake_req, claims=claims, db=db
        ) == {"ret": "*1"}
        assert await api_wf_l2.delete_resource(r.id, "interface/vpls", "*1", fake_req, claims=claims, db=db) == {
            "ret": "*1"
        }


# ============================================================================
# WEBFIG COMMON HELPERS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_common_helpers(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    t_id = r.tenant_id
    u_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.SUPPORT_L1.value}

    # 1. _check_router_permission without perm raises 403
    mock_exec = MagicMock()
    mock_exec.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_exec
    with pytest.raises(HTTPException) as exc1:
        await api_wf_common._check_router_permission(db, t_id, u_id, r.id, claims)
    assert exc1.value.status_code == 403

    # 2. _create_client_from_vault when r.vault is None raises 400
    r_no_vault = Router(id=r.id, tenant_id=t_id, display_name="R1", api_base_url="https://1.1.1.1:443")
    with pytest.raises(HTTPException) as exc2:
        api_wf_common._create_client_from_vault(r_no_vault, t_id)
    assert exc2.value.status_code == 400

    # 3. get_router_and_client when router not found raises 404
    admin_claims = {"tid": str(t_id), "sub": str(u_id), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    mock_exec.scalar_one_or_none.return_value = None
    with pytest.raises(HTTPException) as exc3:
        await api_wf_common.get_router_and_client(r.id, admin_claims, db)
    assert exc3.value.status_code == 404

    # 4. cached_mikrotik_get with invalid JSON in redis
    fake_redis = AsyncMock()
    fake_redis.get.return_value = "invalid_json{"
    client.get.return_value = {"key": "val"}
    res = await api_wf_common.cached_mikrotik_get(fake_redis, t_id, r.id, "/system/resource", client, refresh=False)
    assert res == {"key": "val"}

    # 5. _create_client_from_vault with previous_password decrypts properly
    r_prev = Router(id=r.id, tenant_id=t_id, display_name="R1", api_base_url="https://1.1.1.1:443", api_port=443)
    aad = f"{t_id}:{r.id}".encode()
    ct_c, iv_c, tag_c = encrypt_aes_gcm(b"cur123", aad)
    ct_p, iv_p, tag_p = encrypt_aes_gcm(b"prev123", aad)
    r_prev.vault = RouterCredentialsVault(
        router_id=r.id,
        tenant_id=t_id,
        api_username="admin",
        current_password_ciphertext=ct_c,
        current_password_iv=iv_c,
        current_password_tag=tag_c,
        previous_password_ciphertext=ct_p,
        previous_password_iv=iv_p,
        previous_password_tag=tag_p,
    )
    cl = api_wf_common._create_client_from_vault(r_prev, t_id)
    assert cl.previous_password == "prev123"
