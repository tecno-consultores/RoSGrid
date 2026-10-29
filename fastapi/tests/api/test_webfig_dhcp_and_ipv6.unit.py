# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite de Pruebas Unitarias para Endpoints DHCPv4 y Pila Dual IPv6 WebFig v7."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

import src.api.v1.webfig_ip as api_wf_ip
import src.api.v1.webfig_ipv6 as api_wf_ipv6
from src.models.inventory import Router
from src.schemas.webfig_l1_net import (
    DhcpClientCreateRequest,
    DhcpClientUpdateRequest,
    DhcpNetworkCreateRequest,
    DhcpNetworkUpdateRequest,
    DhcpServerCreateRequest,
    DhcpServerUpdateRequest,
    Ipv6AddressCreateRequest,
    Ipv6DhcpClientCreateRequest,
    Ipv6DhcpServerCreateRequest,
    Ipv6PoolCreateRequest,
)


@pytest.fixture
def fake_client_and_router() -> tuple[Router, AsyncMock]:
    t_id = uuid.uuid4()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=t_id,
        display_name="Edge-DHCP-IPv6-Test",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
    )
    client = AsyncMock()
    client.get.return_value = [{"name": "dhcp1", ".id": "*1", "disabled": "false"}]
    client.post.return_value = {"ret": "*1"}
    client.put.return_value = {"ret": "*1"}
    client.patch.return_value = {"ret": "*1"}
    client.delete.return_value = {}
    client.close = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return r, client


# ============================================================================
# DHCPv4 SERVER, NETWORKS & CLIENTS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_dhcp_servers_crud(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List DHCP Servers
        res_list = await api_wf_ip.list_dhcp_servers(r.id, refresh=True, claims=claims, db=db)
        assert len(res_list) == 1
        assert res_list[0]["name"] == "dhcp1"

        # 2. Create DHCP Server
        create_payload = DhcpServerCreateRequest(
            name="dhcp-lan",
            interface="bridge1",
            address_pool="pool-lan",
            lease_time="12h",
            disabled=False,
        )
        res_create = await api_wf_ip.create_dhcp_server(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Update DHCP Server
        update_payload = DhcpServerUpdateRequest(
            lease_time="24h",
            disabled=True,
        )
        res_update = await api_wf_ip.update_dhcp_server(r.id, "*1", update_payload, claims=claims, db=db)
        assert res_update == {"ret": "*1"}

        # 4. Delete DHCP Server
        res_del = await api_wf_ip.delete_dhcp_server(r.id, "*1", claims=claims, db=db)
        assert res_del == {}


@pytest.mark.asyncio
async def test_webfig_dhcp_networks_crud(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List DHCP Networks
        res_list = await api_wf_ip.list_dhcp_networks(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_list, list)

        # 2. Create DHCP Network
        create_payload = DhcpNetworkCreateRequest(
            address="192.168.88.0/24",
            gateway="192.168.88.1",
            dns_server="8.8.8.8,1.1.1.1",
            domain="lan.corp",
            comment="LAN Corporativa",
        )
        res_create = await api_wf_ip.create_dhcp_network(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Update DHCP Network
        update_payload = DhcpNetworkUpdateRequest(
            dns_server="1.1.1.1",
            comment="Actualizado",
        )
        res_update = await api_wf_ip.update_dhcp_network(r.id, "*net1", update_payload, claims=claims, db=db)
        assert res_update == {"ret": "*1"}

        # 4. Delete DHCP Network
        res_del = await api_wf_ip.delete_dhcp_network(r.id, "*net1", claims=claims, db=db)
        assert res_del == {}


@pytest.mark.asyncio
async def test_webfig_dhcp_clients_crud_and_actions(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List DHCP Clients
        res_list = await api_wf_ip.list_dhcp_clients(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_list, list)

        # 2. Create DHCP Client
        create_payload = DhcpClientCreateRequest(
            interface="ether1",
            add_default_route=True,
            use_peer_dns=True,
            use_peer_ntp=True,
            disabled=False,
            comment="WAN DHCP",
        )
        res_create = await api_wf_ip.create_dhcp_client(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Update DHCP Client
        update_payload = DhcpClientUpdateRequest(
            add_default_route=False,
            disabled=True,
        )
        res_update = await api_wf_ip.update_dhcp_client(r.id, "*c1", update_payload, claims=claims, db=db)
        assert res_update == {"ret": "*1"}

        # 4. Renew DHCP Client
        res_renew = await api_wf_ip.renew_dhcp_client(r.id, "*c1", claims=claims, db=db)
        assert res_renew == {"ret": "*1"}

        # 5. Release DHCP Client
        res_rel = await api_wf_ip.release_dhcp_client(r.id, "*c1", claims=claims, db=db)
        assert res_rel == {"ret": "*1"}

        # 6. Delete DHCP Client
        res_del = await api_wf_ip.delete_dhcp_client(r.id, "*c1", claims=claims, db=db)
        assert res_del == {}


# ============================================================================
# IPv6 ADDRESSES, DHCPv6 CLIENT/SERVER, POOLS & NDP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_webfig_ipv6_addresses_crud(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ipv6.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ipv6.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List IPv6 Addresses
        res_list = await api_wf_ipv6.list_ipv6_addresses(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_list, list)

        # 2. Create IPv6 Address
        create_payload = Ipv6AddressCreateRequest(
            address="2001:db8:acad::1/64",
            interface="ether2",
            advertise=True,
            eui_64=False,
            disabled=False,
            comment="NOC IPv6",
        )
        res_create = await api_wf_ipv6.create_ipv6_address(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Delete IPv6 Address
        res_del = await api_wf_ipv6.delete_ipv6_address(r.id, "*v6_1", claims=claims, db=db)
        assert res_del == {}


@pytest.mark.asyncio
async def test_webfig_ipv6_dhcp_client_crud(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ipv6.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ipv6.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List DHCPv6 Clients
        res_list = await api_wf_ipv6.list_ipv6_dhcp_clients(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_list, list)

        # 2. Create DHCPv6 Client
        create_payload = Ipv6DhcpClientCreateRequest(
            interface="ether1",
            request="prefix",
            pool_name="pool-v6-delegated",
            pool_prefix_length=64,
            add_default_route=True,
            disabled=False,
            comment="ISP PD",
        )
        res_create = await api_wf_ipv6.create_ipv6_dhcp_client(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Delete DHCPv6 Client
        res_del = await api_wf_ipv6.delete_ipv6_dhcp_client(r.id, "*v6_c1", claims=claims, db=db)
        assert res_del == {}


@pytest.mark.asyncio
async def test_webfig_ipv6_dhcp_server_crud(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ipv6.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ipv6.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List DHCPv6 Servers
        res_list = await api_wf_ipv6.list_ipv6_dhcp_servers(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_list, list)

        # 2. Create DHCPv6 Server
        create_payload = Ipv6DhcpServerCreateRequest(
            name="dhcp6-server-lan",
            interface="bridge1",
            address_pool="pool-v6-delegated",
            lease_time="24h",
            disabled=False,
        )
        res_create = await api_wf_ipv6.create_ipv6_dhcp_server(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Delete DHCPv6 Server
        res_del = await api_wf_ipv6.delete_ipv6_dhcp_server(r.id, "*v6_s1", claims=claims, db=db)
        assert res_del == {}


@pytest.mark.asyncio
async def test_webfig_ipv6_pools_and_ndp(fake_client_and_router: tuple[Router, AsyncMock]) -> None:
    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "tenant_admin"}

    with (
        patch("src.api.v1.webfig_ipv6.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ipv6.get_redis_client", return_value=AsyncMock(get=AsyncMock(return_value=None))),
    ):
        # 1. List IPv6 Pools
        res_list = await api_wf_ipv6.list_ipv6_pools(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_list, list)

        # 2. Create IPv6 Pool
        create_payload = Ipv6PoolCreateRequest(
            name="pool6-static",
            prefix="2001:db8:cafe::/48",
            prefix_length=64,
        )
        res_create = await api_wf_ipv6.create_ipv6_pool(r.id, create_payload, claims=claims, db=db)
        assert res_create == {"ret": "*1"}

        # 3. Delete IPv6 Pool
        res_del = await api_wf_ipv6.delete_ipv6_pool(r.id, "*v6_p1", claims=claims, db=db)
        assert res_del == {}

        # 4. List IPv6 Neighbors (NDP)
        res_neigh = await api_wf_ipv6.list_ipv6_neighbors(r.id, refresh=True, claims=claims, db=db)
        assert isinstance(res_neigh, list)

        # 5. List IPv6 ND Settings (Router Advertisements)
        res_nd = await api_wf_ipv6.list_ipv6_nd_settings(r.id, claims=claims, db=db)
        assert isinstance(res_nd, list)


@pytest.mark.asyncio
async def test_webfig_dhcp_idempotent_creation_on_duplicate(
    fake_client_and_router: tuple[Router, AsyncMock],
) -> None:
    from src.mikrotik.client import MikrotikApiError
    from src.schemas.webfig_l1_net import IpPoolCreateRequest

    r, client = fake_client_and_router
    db = AsyncMock()
    claims = {"tid": str(r.tenant_id), "sub": str(uuid.uuid4()), "rol": "SUPPORT_L2"}

    async def _put_side_effect(endpoint: str, *args: object, **kwargs: object) -> dict[str, str]:
        if endpoint in {"/ip/pool", "/ip/dhcp-server/network", "/ip/dhcp-server"}:
            raise MikrotikApiError(400, "failure: already exists")
        return {".id": "*sched1"}

    client.put.side_effect = _put_side_effect
    client.get.return_value = [
        {
            ".id": "*existing1",
            "name": "pool-ether1",
            "address": "192.168.88.0/24",
            "interface": "ether1",
        }
    ]
    client.patch.return_value = {"ret": "*existing1"}

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.invalidate_webfig_cache", new_callable=AsyncMock),
    ):
        res_pool = await api_wf_ip.create_pool(
            r.id,
            IpPoolCreateRequest(name="pool-ether1", ranges="192.168.88.10-192.168.88.254"),
            claims=claims,
            db=db,
        )
        assert res_pool == {"ret": "*existing1"}

        res_net = await api_wf_ip.create_dhcp_network(
            r.id,
            DhcpNetworkCreateRequest(
                address="192.168.88.0/24", gateway="192.168.88.1", dns_server="8.8.8.8"
            ),
            claims=claims,
            db=db,
        )
        assert res_net == {"ret": "*existing1"}

        res_srv = await api_wf_ip.create_dhcp_server(
            r.id,
            DhcpServerCreateRequest(
                name="dhcp-ether1",
                interface="ether1",
                address_pool="pool-ether1",
                lease_time="12h",
                disabled=False,
            ),
            claims=claims,
            db=db,
        )
        assert res_srv == {"ret": "*existing1"}
