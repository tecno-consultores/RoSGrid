# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Bridge VLAN Filtering (/interface/bridge/vlan), Subinterfaces VLAN (/interface/vlan) y Firewall parity."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.api.v1.webfig_firewall import list_rules
from src.api.v1.webfig_interfaces import (
    create_bridge_vlan,
    create_vlan,
    delete_bridge_vlan,
    delete_vlan,
    update_bridge_vlan,
)
from src.schemas.webfig_l1_net import (
    BridgeVlanCreateRequest,
    BridgeVlanUpdateRequest,
    VlanCreateRequest,
)


@pytest.fixture
def mock_claims() -> dict:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(uuid.uuid4()),
        "rol": "SUPERADMIN_GLOBAL",
    }


@pytest.mark.asyncio
async def test_create_bridge_vlan_safe_mode(mock_claims: dict):
    router_id = uuid.uuid4()
    payload = BridgeVlanCreateRequest(
        bridge="bridge-lan",
        vlan_ids="10,20,30",
        tagged="ether1,bridge-lan",
        untagged="ether2",
        comment="VLANs Corporativas",
        disabled=False,
    )
    mock_db = AsyncMock()
    mock_client = AsyncMock()
    mock_client.put.return_value = {"ret": "*1"}

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(AsyncMock(), mock_client)),
        patch("src.api.v1.webfig_interfaces.execute_safe_mutation", new_callable=AsyncMock) as mock_safe,
    ):
        mock_safe.return_value = {"status": "success", "action": "create", "menu": "interface/bridge/vlan"}
        res = await create_bridge_vlan(
            router_id=router_id,
            payload=payload,
            claims=mock_claims,
            db=mock_db,
        )
        assert res["status"] == "success"
        assert res["menu"] == "interface/bridge/vlan"
        mock_safe.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_and_delete_bridge_vlan(mock_claims: dict):
    router_id = uuid.uuid4()
    item_id = "*A1"
    patch_payload = BridgeVlanUpdateRequest(
        vlan_ids="10-50",
        tagged="ether1,sfp-sfpplus1",
        comment="Rango Expandido",
    )
    mock_db = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get.return_value = {"vlan-ids": "10"}

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(AsyncMock(), mock_client)),
        patch("src.api.v1.webfig_interfaces.execute_safe_mutation", new_callable=AsyncMock) as mock_safe,
    ):
        mock_safe.return_value = {"status": "success", "action": "set"}
        res_update = await update_bridge_vlan(
            router_id=router_id,
            item_id=item_id,
            payload=patch_payload,
            claims=mock_claims,
            db=mock_db,
        )
        assert res_update["status"] == "success"

        mock_safe.return_value = {"status": "success", "action": "delete"}
        res_del = await delete_bridge_vlan(
            router_id=router_id,
            item_id=item_id,
            claims=mock_claims,
            db=mock_db,
        )
        assert res_del["status"] == "success"


@pytest.mark.asyncio
async def test_create_and_delete_interface_vlan(mock_claims: dict):
    router_id = uuid.uuid4()
    payload = VlanCreateRequest(
        name="vlan100-mgmt",
        vlan_id=100,
        interface="bridge-lan",
        mtu=1500,
        comment="Management VLAN",
    )
    mock_db = AsyncMock()
    mock_client = AsyncMock()

    with (
        patch("src.api.v1.webfig_interfaces.get_router_and_client", return_value=(AsyncMock(), mock_client)),
        patch("src.api.v1.webfig_interfaces.execute_safe_mutation", new_callable=AsyncMock) as mock_safe,
    ):
        mock_safe.return_value = {"status": "success", "action": "create", "menu": "interface/vlan"}
        res_create = await create_vlan(
            router_id=router_id,
            payload=payload,
            claims=mock_claims,
            db=mock_db,
        )
        assert res_create["status"] == "success"

        mock_safe.return_value = {"status": "success", "action": "delete"}
        res_del = await delete_vlan(
            router_id=router_id,
            item_id="*VLAN1",
            claims=mock_claims,
            db=mock_db,
        )
        assert res_del["status"] == "success"


@pytest.mark.asyncio
async def test_firewall_list_rules_address_lists_and_connections_delegation(mock_claims: dict):
    router_id = uuid.uuid4()
    mock_db = AsyncMock()

    with (
        patch("src.api.v1.webfig_firewall.list_address_lists", new_callable=AsyncMock) as mock_addr,
        patch("src.api.v1.webfig_firewall.list_connections", new_callable=AsyncMock) as mock_conn,
    ):
        mock_addr.return_value = [{"list": "blocklist", "address": "192.168.1.50"}]
        mock_conn.return_value = [{"protocol": "tcp", "src-address": "10.0.0.2", "dst-address": "8.8.8.8"}]

        # Test address-list call
        res_addr = await list_rules(
            router_id=router_id,
            proto="ip",
            table_type="address-list",
            refresh=False,
            claims=mock_claims,
            db=mock_db,
        )
        assert len(res_addr) == 1
        assert res_addr[0]["list"] == "blocklist"
        mock_addr.assert_awaited_once()

        # Test connections call
        res_conn = await list_rules(
            router_id=router_id,
            proto="ip",
            table_type="connections",
            refresh=False,
            claims=mock_claims,
            db=mock_db,
        )
        assert len(res_conn) == 1
        assert res_conn[0]["protocol"] == "tcp"
        mock_conn.assert_awaited_once()
