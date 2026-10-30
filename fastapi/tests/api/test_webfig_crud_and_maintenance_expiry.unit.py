# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite de pruebas unitarias para paridad CRUD WebFig v7 (Bridge, WireGuard, IP/DHCP/Pools/DNS, PPPoE, IPv6, Routing, Firewall) y auto-expiración WORM de ventanas de mantenimiento."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.api.v1.maintenance as api_maint
import src.api.v1.webfig_firewall as api_wf_fw
import src.api.v1.webfig_interfaces as api_wf_if
import src.api.v1.webfig_ip as api_wf_ip
import src.api.v1.webfig_ipv6 as api_wf_ipv6
import src.api.v1.webfig_ppp as api_wf_ppp
import src.api.v1.webfig_routing as api_wf_rt
from src.models.inventory import MaintenanceWindow, Router
from src.schemas.webfig_firewall import (
    AddressListUpdateRequest,
    RoutingRuleUpdateRequest,
    RoutingTableUpdateRequest,
)
from src.schemas.webfig_l1_net import (
    BridgePortUpdateRequest,
    DhcpClientUpdateRequest,
    DhcpNetworkUpdateRequest,
    DnsSettingsUpdateRequest,
    DnsStaticCreateRequest,
    DnsStaticUpdateRequest,
    IpArpUpdateRequest,
    IpPoolUpdateRequest,
    Ipv6AddressUpdateRequest,
    Ipv6DhcpClientUpdateRequest,
    Ipv6DhcpServerUpdateRequest,
    Ipv6PoolUpdateRequest,
    WireGuardPeerUpdateRequest,
    WireGuardUpdateRequest,
)
from src.schemas.webfig_ops import (
    PppoeServerUpdateRequest,
    PppProfileUpdateRequest,
    PppSecretUpdateRequest,
)


@pytest.fixture
def mock_claims() -> dict:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(uuid.uuid4()),
        "rol": "SUPERADMIN_GLOBAL",
    }


@pytest.fixture
def fake_router_and_client(mock_claims: dict) -> tuple[Router, AsyncMock]:
    r = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(mock_claims["tid"]),
        display_name="CCR2004-WebFig-FullCRUD",
        api_base_url="https://10.255.0.1:443",
        api_port=443,
    )
    client = AsyncMock()
    client.get.return_value = {"name": "item1", ".id": "*1", "disabled": "false"}
    client.post.return_value = {"ret": "*1"}
    client.put.return_value = {"ret": "*1"}
    client.patch.return_value = {"ret": "*1"}
    client.delete.return_value = {}
    client.close = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return r, client


@pytest.mark.asyncio
async def test_bridge_and_ports_delete_and_edit_parity(
    fake_router_and_client: tuple[Router, AsyncMock],
    mock_claims: dict,
) -> None:
    """Verifica eliminar un bridge, editar un puerto de bridge y sacar un puerto de un bridge (DELETE /bridge/ports/{id})."""
    r, client = fake_router_and_client
    db = AsyncMock()

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(r, client)),
        patch(
            "src.api.v1.webfig_interfaces.execute_safe_mutation",
            new_callable=AsyncMock,
            return_value={"status": "success"},
        ) as mock_safe,
    ):
        # 1. Eliminar Bridge
        res_del_br = await api_wf_if.delete_bridge(r.id, "*BR1", claims=mock_claims, db=db)
        assert res_del_br["status"] == "success"

        # 2. Editar puerto miembro de Bridge (PVID, frame-types, ingress-filtering,horizon, comment)
        port_patch = BridgePortUpdateRequest(
            bridge="bridge-core",
            interface="ether2",
            pvid=200,
            frame_types="admit-only-untagged-and-priority-tagged",
            ingress_filtering=True,
            hw=True,
            horizon="1",
            disabled=False,
            comment="Acceso Corporativo VLAN 200",
        )
        res_upd_port = await api_wf_if.update_bridge_port(
            r.id,
            "*BP1",
            port_patch,
            claims=mock_claims,
            db=db,
        )
        assert res_upd_port["status"] == "success"

        # 3. Sacar un puerto de un Bridge (DELETE /bridge/ports/{item_id})
        res_del_port = await api_wf_if.delete_bridge_port(
            r.id,
            "*BP1",
            claims=mock_claims,
            db=db,
        )
        assert res_del_port["status"] == "success"
        assert mock_safe.await_count == 3


@pytest.mark.asyncio
async def test_wireguard_tunnel_and_peers_edit_and_delete_parity(
    fake_router_and_client: tuple[Router, AsyncMock],
    mock_claims: dict,
) -> None:
    """Verifica editar y eliminar interfaces de túnel WireGuard y sus Peers."""
    r, client = fake_router_and_client
    db = AsyncMock()

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(r, client)),
        patch(
            "src.api.v1.webfig_interfaces.execute_safe_mutation",
            new_callable=AsyncMock,
            return_value={"status": "success"},
        ) as mock_safe,
    ):
        # 1. Editar túnel WireGuard
        wg_patch = WireGuardUpdateRequest(
            name="wg-backbone",
            listen_port=51820,
            mtu=1420,
            disabled=False,
            comment="Túnel Sitio A",
        )
        res_upd_wg = await api_wf_if.update_wireguard(r.id, "*WG1", wg_patch, claims=mock_claims, db=db)
        assert res_upd_wg["status"] == "success"

        # 2. Eliminar túnel WireGuard
        res_del_wg = await api_wf_if.delete_wireguard(r.id, "*WG1", claims=mock_claims, db=db)
        assert res_del_wg["status"] == "success"

        # 3. Editar Peer WireGuard
        peer_patch = WireGuardPeerUpdateRequest(
            interface="wg-backbone",
            public_key="a" * 43 + "=",
            allowed_address="10.99.0.2/32",
            endpoint_address="203.0.113.10",
            endpoint_port=51820,
            persistent_keepalive="25s",
            disabled=False,
            comment="Peer Remoto Sucursal",
        )
        res_upd_peer = await api_wf_if.update_wireguard_peer(
            r.id,
            "*WGP1",
            peer_patch,
            claims=mock_claims,
            db=db,
        )
        assert res_upd_peer["status"] == "success"

        # 4. Eliminar Peer WireGuard
        res_del_peer = await api_wf_if.delete_wireguard_peer(
            r.id,
            "*WGP1",
            claims=mock_claims,
            db=db,
        )
        assert res_del_peer["status"] == "success"
        assert mock_safe.await_count == 4


@pytest.mark.asyncio
async def test_ip_pools_dns_arp_and_dhcp_full_edit_delete_parity(
    fake_router_and_client: tuple[Router, AsyncMock],
    mock_claims: dict,
) -> None:
    """Verifica edición y eliminación de Pools IP, parámetros DNS, registros DNS estáticos, ARP y redes/clientes DHCP."""
    r, client = fake_router_and_client
    db = AsyncMock()
    fake_redis = AsyncMock(get=AsyncMock(return_value=None), delete=AsyncMock())

    with (
        patch("src.api.v1.webfig_ip.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ip.get_redis_client", return_value=fake_redis),
    ):
        # 1. Editar y eliminar Pool de conexiones IP
        pool_patch = IpPoolUpdateRequest(
            name="pool-clientes-vip",
            ranges="10.20.0.10-10.20.0.250",
            next_pool="pool-fallback",
            comment="Pool FTTH VIP",
        )
        res_upd_pool = await api_wf_ip.update_pool(r.id, "*P1", pool_patch, claims=mock_claims, db=db)
        assert res_upd_pool == {"ret": "*1"}

        res_del_pool = await api_wf_ip.delete_pool(r.id, "*P1", claims=mock_claims, db=db)
        assert res_del_pool == {}

        # 2. Editar parámetros globales de DNS (Singleton /ip/dns/set)
        dns_patch = DnsSettingsUpdateRequest(
            servers="1.1.1.1,8.8.8.8",
            allow_remote_requests=True,
            cache_size=4096,
            max_udp_packet_size=4096,
            use_doh_server="https://cloudflare-dns.com/dns-query",
            verify_doh_cert=True,
        )
        res_dns = await api_wf_ip.update_dns_settings(r.id, dns_patch, claims=mock_claims, db=db)
        assert res_dns == {"ret": "*1"}

        # 3. Crear, editar y eliminar registro DNS estático
        dns_static_create = DnsStaticCreateRequest(
            name="core.rosgrid.lan",
            address="192.168.88.1",
            ttl="1d",
            disabled=False,
            comment="Gateway Local",
        )
        res_dns_create = await api_wf_ip.create_dns_static(r.id, dns_static_create, claims=mock_claims, db=db)
        assert res_dns_create == {"ret": "*1"}

        dns_static_upd = DnsStaticUpdateRequest(
            name="core-nuevo.rosgrid.lan",
            address="192.168.88.2",
            ttl="12h",
            disabled=True,
            comment="Actualizado",
        )
        res_dns_upd = await api_wf_ip.update_dns_static(r.id, "*DNS1", dns_static_upd, claims=mock_claims, db=db)
        assert res_dns_upd == {"ret": "*1"}

        res_dns_del = await api_wf_ip.delete_dns_static(r.id, "*DNS1", claims=mock_claims, db=db)
        assert res_dns_del == {}

        # 4. Editar entrada ARP estática
        arp_upd = IpArpUpdateRequest(
            address="192.168.88.55",
            mac_address="AA:BB:CC:DD:EE:FF",
            interface="bridge1",
            disabled=False,
            comment="Servidor NAS",
        )
        res_arp_upd = await api_wf_ip.update_arp(r.id, "*ARP1", arp_upd, claims=mock_claims, db=db)
        assert res_arp_upd == {"ret": "*1"}

        # 5. Editar red DHCP con todos sus campos (address, gateway, dns_server, domain, ntp_server, comment)
        net_upd = DhcpNetworkUpdateRequest(
            address="192.168.90.0/24",
            gateway="192.168.90.1",
            dns_server="1.1.1.1,9.9.9.9",
            domain="sucursal.lan",
            ntp_server="192.168.90.1",
            comment="Red DHCP Editada",
        )
        res_net_upd = await api_wf_ip.update_dhcp_network(r.id, "*NET1", net_upd, claims=mock_claims, db=db)
        assert res_net_upd == {"ret": "*1"}

        # 6. Editar cliente DHCP con todos sus campos
        cli_upd = DhcpClientUpdateRequest(
            interface="ether1",
            add_default_route=True,
            use_peer_dns=False,
            use_peer_ntp=True,
            default_route_distance=2,
            disabled=False,
            comment="WAN Secundaria",
        )
        res_cli_upd = await api_wf_ip.update_dhcp_client(r.id, "*CLI1", cli_upd, claims=mock_claims, db=db)
        assert res_cli_upd == {"ret": "*1"}


@pytest.mark.asyncio
async def test_ppp_ipv6_routing_and_firewall_edit_delete_parity(
    fake_router_and_client: tuple[Router, AsyncMock],
    mock_claims: dict,
) -> None:
    """Verifica edición y eliminación completa en PPPoE, IPv6, Routing y Firewall Address-Lists."""
    r, client = fake_router_and_client
    db = AsyncMock()
    fake_redis = AsyncMock(get=AsyncMock(return_value=None), delete=AsyncMock())

    # 1. PPPoE Secrets, Profiles y PPPoE Servers
    with (
        patch("src.api.v1.webfig_ppp.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ppp.get_redis_client", return_value=fake_redis),
    ):
        sec_upd = PppSecretUpdateRequest(
            name="cliente-ftth-01",
            password="NuevaPasswordSegura123",
            profile="plan-500m",
            service="pppoe",
            local_address="10.10.0.1",
            remote_address="10.10.0.50",
            routes="192.168.200.0/24 10.10.0.50 1",
            disabled=False,
            comment="Suscriptor Empresarial",
        )
        res_sec = await api_wf_ppp.update_secret(r.id, "*SEC1", sec_upd, claims=mock_claims, db=db)
        assert res_sec == {"ret": "*1"}

        prof_upd = PppProfileUpdateRequest(
            name="plan-500m",
            local_address="10.10.0.1",
            remote_address="pool-ftth",
            rate_limit="500M/500M",
            dns_server="1.1.1.1",
            only_one="yes",
            comment="Perfil Simétrico 500M",
        )
        res_prof = await api_wf_ppp.update_profile(r.id, "*PROF1", prof_upd, claims=mock_claims, db=db)
        assert res_prof == {"ret": "*1"}

        res_prof_del = await api_wf_ppp.delete_profile(r.id, "*PROF1", claims=mock_claims, db=db)
        assert res_prof_del == {}

        srv_upd = PppoeServerUpdateRequest(
            service_name="isp-concentrador-norte",
            interface="vlan200-ftth",
            default_profile="plan-500m",
            authentication="chap,mschap2",
            one_session_per_host=True,
            max_mtu=1492,
            max_mru=1492,
            disabled=False,
        )
        res_srv_upd = await api_wf_ppp.update_pppoe_server(r.id, "*SRV1", srv_upd, claims=mock_claims, db=db)
        assert res_srv_upd == {"ret": "*1"}

        res_srv_del = await api_wf_ppp.delete_pppoe_server(r.id, "*SRV1", claims=mock_claims, db=db)
        assert res_srv_del == {}

    # 2. IPv6 Addresses, DHCPv6 Clients, DHCPv6 Servers y Pools IPv6
    with (
        patch("src.api.v1.webfig_ipv6.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_ipv6.get_redis_client", return_value=fake_redis),
    ):
        v6_addr_upd = Ipv6AddressUpdateRequest(
            address="2001:db8:100::1/64",
            interface="bridge1",
            advertise=True,
            eui_64=False,
            disabled=False,
            comment="Gateway LAN v6",
        )
        assert await api_wf_ipv6.update_ipv6_address(r.id, "*V6A1", v6_addr_upd, claims=mock_claims, db=db) == {
            "ret": "*1"
        }

        v6_cli_upd = Ipv6DhcpClientUpdateRequest(
            interface="ether1",
            request="address,prefix",
            pool_name="pool-isp-v6",
            pool_prefix_length=64,
            add_default_route=True,
            use_peer_dns=True,
            disabled=False,
            comment="PD WAN1",
        )
        assert await api_wf_ipv6.update_ipv6_dhcp_client(r.id, "*V6C1", v6_cli_upd, claims=mock_claims, db=db) == {
            "ret": "*1"
        }

        v6_srv_upd = Ipv6DhcpServerUpdateRequest(
            name="dhcpv6-lan",
            interface="bridge1",
            address_pool="pool-isp-v6",
            lease_time="1d",
            disabled=False,
            comment="Servidor DHCPv6",
        )
        assert await api_wf_ipv6.update_ipv6_dhcp_server(r.id, "*V6S1", v6_srv_upd, claims=mock_claims, db=db) == {
            "ret": "*1"
        }

        v6_pool_upd = Ipv6PoolUpdateRequest(
            name="pool-v6-corp",
            prefix="2001:db8:abcd::/48",
            prefix_length=64,
            comment="Pool Delegado",
        )
        assert await api_wf_ipv6.update_ipv6_pool(r.id, "*V6P1", v6_pool_upd, claims=mock_claims, db=db) == {
            "ret": "*1"
        }

    # 3. Routing Tables, PBR Rules y Filter Rules
    with (
        patch("src.api.v1.webfig_routing.get_router_and_client", return_value=(r, client)),
        patch(
            "src.api.v1.webfig_routing.execute_safe_mutation",
            new_callable=AsyncMock,
            return_value={"status": "success"},
        ),
    ):
        tbl_upd = RoutingTableUpdateRequest(name="vrf-clientes", fib=True, disabled=False, comment="Tabla VRF")
        assert (await api_wf_rt.update_table(r.id, "*T1", tbl_upd, claims=mock_claims, db=db))["status"] == "success"
        assert (await api_wf_rt.delete_table(r.id, "*T1", claims=mock_claims, db=db))["status"] == "success"

        rule_upd = RoutingRuleUpdateRequest(
            src_address="10.50.0.0/24",
            dst_address="0.0.0.0/0",
            action="lookup-only-in-table",
            table="vrf-clientes",
            disabled=False,
            comment="PBR Salida VRF",
        )
        assert (await api_wf_rt.update_rule(r.id, "*R1", rule_upd, claims=mock_claims, db=db))["status"] == "success"
        assert (await api_wf_rt.delete_rule(r.id, "*R1", claims=mock_claims, db=db))["status"] == "success"
        assert (await api_wf_rt.delete_filter_rule(r.id, "*F1", claims=mock_claims, db=db))["status"] == "success"

    # 4. Firewall Address-List Update
    with (
        patch("src.api.v1.webfig_firewall.get_router_and_client", return_value=(r, client)),
        patch("src.api.v1.webfig_firewall.get_redis_client", return_value=fake_redis),
        patch("src.api.v1.webfig_firewall.invalidate_webfig_cache", new_callable=AsyncMock),
        patch(
            "src.api.v1.webfig_firewall.execute_safe_mutation",
            new_callable=AsyncMock,
            return_value={"status": "success"},
        ),
    ):
        al_upd = AddressListUpdateRequest(
            list="NOC_TRUSTED",
            address="10.88.0.0/24",
            timeout="1d",
            disabled=False,
            comment="Subred Gestión NOC",
        )
        res_al = await api_wf_fw.update_address_list(
            router_id=r.id,
            proto="ip",
            item_id="*AL1",
            payload=al_upd,
            claims=mock_claims,
            db=db,
        )
        assert res_al["status"] == "success"


@pytest.mark.asyncio
async def test_maintenance_windows_auto_expiration_and_worm_audit_log() -> None:
    """Verifica que las ventanas de mantenimiento vencidas se eliminen automáticamente y dejen registro WORM en AuditLog."""
    now_utc = datetime.now(UTC)
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    router_id = uuid.uuid4()

    expired_window = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        router_id=router_id,
        title="Mantenimiento Nocturno Vencido",
        reason="Reinicio programado de CCR",
        starts_at=now_utc - timedelta(hours=3),
        ends_at=now_utc - timedelta(minutes=15),
        suppress_alerts=True,
        is_cancelled=False,
        created_by=user_id,
        created_at=now_utc - timedelta(hours=4),
    )

    active_window = MaintenanceWindow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        router_id=router_id,
        title="Mantenimiento Futuro Vigente",
        reason="Cambio de transceptor SFP+",
        starts_at=now_utc - timedelta(minutes=10),
        ends_at=now_utc + timedelta(hours=2),
        suppress_alerts=True,
        is_cancelled=False,
        created_by=user_id,
        created_at=now_utc - timedelta(minutes=30),
    )

    # 1. Validar predicado _is_window_expired (con tzinfo y naive datetime)
    assert api_maint._is_window_expired(expired_window, now_utc) is True
    assert api_maint._is_window_expired(active_window, now_utc) is False

    naive_expired = MagicMock(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Naive Expired",
        starts_at=(now_utc - timedelta(hours=2)).replace(tzinfo=None),
        ends_at=(now_utc - timedelta(minutes=1)).replace(tzinfo=None),
    )
    assert api_maint._is_window_expired(naive_expired, now_utc) is True

    # 2. Validar purge_expired_maintenance_windows (usado por health_monitor_worker)
    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [expired_window]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    with patch("src.api.v1.maintenance.write_audit_log", new_callable=AsyncMock) as mock_audit:
        purged_count = await api_maint.purge_expired_maintenance_windows(
            mock_session,
            tenant_id=tenant_id,
            commit=True,
        )
        assert purged_count == 1
        mock_audit.assert_awaited_once()
        audit_kwargs = mock_audit.await_args.kwargs
        assert audit_kwargs["event_category"] == "OPERATIONS"
        assert audit_kwargs["event_action"] == "MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED"
        assert audit_kwargs["before_state"]["title"] == "Mantenimiento Nocturno Vencido"
        assert audit_kwargs["after_state"]["status"] == "EXPIRED_AND_DELETED"
        mock_session.delete.assert_awaited_once_with(expired_window)
        mock_session.commit.assert_awaited_once()

    # 3. Validar list_maintenance_windows purgando reactivamente las vencidas y devolviendo solo las vigentes
    mock_db = AsyncMock()
    mock_scalars_list = MagicMock()
    mock_scalars_list.all.return_value = [expired_window, active_window]
    mock_result_list = MagicMock()
    mock_result_list.scalars.return_value = mock_scalars_list
    mock_db.execute.return_value = mock_result_list

    claims = {"tid": str(tenant_id), "sub": str(user_id), "rol": "TENANT_ADMIN"}
    with patch("src.api.v1.maintenance.write_audit_log", new_callable=AsyncMock) as mock_audit_list:
        returned = await api_maint.list_maintenance_windows(
            router_id=None,
            is_active=None,
            is_cancelled=None,
            claims=claims,
            db=mock_db,
        )
        assert len(returned) == 1
        assert returned[0].id == active_window.id
        assert returned[0].title == "Mantenimiento Futuro Vigente"
        mock_audit_list.assert_awaited_once()
        mock_db.delete.assert_awaited_once_with(expired_window)
        mock_db.commit.assert_awaited_once()
