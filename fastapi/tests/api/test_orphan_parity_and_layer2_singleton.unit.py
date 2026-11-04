# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Paridad de Endpoints Operativos y WebFig Singleton (Hito 28.5).
Cubre:
1. Alias retrocompatible de rotación de credenciales de bóveda (POST /vault/routers/{id}/rotate).
2. Alias retrocompatible de re-pinning SSL TOFU (POST /vault/routers/{id}/repin-ssl).
3. Decoradores y endpoints alternativos de SD-WAN (/spokes y /multi-wan/failover).
4. Mutaciones singleton en WebFig Capa 2 (/singleton/{ros_path} y fallback en /resource/{ros_path}).
5. Eliminación de conexiones activas en Firewall Conntrack (DELETE /connections/{conn_id}).
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from src.api.v1.inventory import repin_ssl, repin_ssl_legacy_alias
from src.api.v1.sdwan import configure_multi_wan_failover, provision_spoke_tunnel
from src.api.v1.vault import rotate_api_key_now_alias, rotate_now
from src.api.v1.webfig_firewall import delete_firewall_connection
from src.api.v1.webfig_layer2 import (
    DynamicLayer2WriteRequest,
    update_resource,
    update_resource_singleton,
)
from src.models.core import SystemRoleEnum
from src.schemas.enterprise import (
    SdwanMultiWanFailoverRequest,
    SdwanProvisionSpokeRequest,
)
from tests.conftest import make_asserting_audit_mock


@pytest.fixture
def superadmin_claims():
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(uuid.uuid4()),
        "role": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
        "rol": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
        "email": "superadmin@example.com",
    }


@pytest.fixture
def mock_db():
    return AsyncMock()


# ==============================================================================
# 1. PRUEBAS DE ALIAS DE BÓVEDA E INVENTARIO
# ==============================================================================


def test_rotate_api_key_now_alias_identity():
    """Verifica que el alias /vault/routers/{id}/rotate apunte idénticamente a rotate_now."""
    assert rotate_api_key_now_alias is rotate_now


def test_repin_ssl_legacy_alias_identity():
    """Verifica que el alias /vault/routers/{id}/repin-ssl apunte idénticamente a repin_ssl."""
    assert repin_ssl_legacy_alias is repin_ssl


# ==============================================================================
# 2. PRUEBAS DE ALIAS Y VALIDACIÓN DE SD-WAN
# ==============================================================================


@pytest.mark.asyncio
async def test_sdwan_spoke_provision_validation(superadmin_claims, mock_db):
    """Verifica que provision_spoke_tunnel valide la existencia de routers en el tenant."""
    payload = SdwanProvisionSpokeRequest(
        hub_router_id=uuid.uuid4(),
        spoke_router_id=uuid.uuid4(),
        spoke_name="Branch-Office-Spoke",
    )
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.client = SimpleNamespace(host="127.0.0.1")

    with pytest.raises(HTTPException) as exc_info:
        await provision_spoke_tunnel(
            payload=payload,
            request=mock_req,
            db=mock_db,
            claims=superadmin_claims,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_sdwan_multi_wan_failover_validation(superadmin_claims, mock_db):
    """Verifica que configure_multi_wan_failover valide la existencia del router."""
    payload = SdwanMultiWanFailoverRequest(
        router_id=uuid.uuid4(),
        primary_wan_interface="ether1",
        backup_wan_interface="ether2",
        check_host="9.9.9.9",
        failover_threshold_ms=120.0,
    )
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.client = SimpleNamespace(host="127.0.0.1")

    with pytest.raises(HTTPException) as exc_info:
        await configure_multi_wan_failover(
            payload=payload,
            request=mock_req,
            db=mock_db,
            claims=superadmin_claims,
        )
    assert exc_info.value.status_code == 404


# ==============================================================================
# 3. PRUEBAS DE RECURSOS SINGLETON EN WEBFIG CAPA 2
# ==============================================================================


@pytest.mark.asyncio
async def test_update_resource_singleton_dedicated_endpoint(superadmin_claims, mock_db):
    """Verifica el endpoint dedicado PATCH /singleton/{ros_path}."""
    router_id = uuid.uuid4()
    req = DynamicLayer2WriteRequest(attributes={"enabled": True}, enable_safemode=False)
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.client = SimpleNamespace(host="127.0.0.1")

    with (
        patch("src.api.v1.webfig_layer2.get_router_and_client", new_callable=AsyncMock) as mock_get_rc,
        patch("src.api.v1.webfig_layer2._get_user_perm", new_callable=AsyncMock) as mock_perm,
        patch("src.api.v1.webfig_layer2.invalidate_webfig_cache", new_callable=AsyncMock),
        patch("src.api.v1.webfig_layer2.write_audit_log", make_asserting_audit_mock()) as mock_l2_audit1,
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = {"ret": "ok"}
        mock_get_rc.return_value = (SimpleNamespace(id=router_id, display_name="Test-Router"), mock_client)
        mock_perm.return_value = SimpleNamespace(can_write_l2=True)

        res = await update_resource_singleton(
            router_id=router_id,
            ros_path="system/ntp/client",
            payload=req,
            request=mock_req,
            claims=superadmin_claims,
            db=mock_db,
        )
        assert res["ret"] == "ok"
        mock_client.post.assert_awaited_once_with("system/ntp/client/set", {"enabled": True})
        mock_l2_audit1.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_resource_singleton_fallback(superadmin_claims, mock_db):
    """Verifica el fallback a singleton cuando update_resource recibe una ruta conocida como 'ip/settings'."""
    router_id = uuid.uuid4()
    req = DynamicLayer2WriteRequest(attributes={"ip-forward": True}, enable_safemode=False)
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.client = SimpleNamespace(host="127.0.0.1")

    with (
        patch("src.api.v1.webfig_layer2.get_router_and_client", new_callable=AsyncMock) as mock_get_rc,
        patch("src.api.v1.webfig_layer2._get_user_perm", new_callable=AsyncMock) as mock_perm,
        patch("src.api.v1.webfig_layer2.invalidate_webfig_cache", new_callable=AsyncMock),
        patch("src.api.v1.webfig_layer2.write_audit_log", make_asserting_audit_mock()) as mock_l2_audit2,
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = {"ret": "ok"}
        mock_get_rc.return_value = (SimpleNamespace(id=router_id, display_name="Test-Router"), mock_client)
        mock_perm.return_value = SimpleNamespace(can_write_l2=True)

        # item_id es 'settings' y ros_path es 'ip' -> ip/settings es singleton conocido
        res = await update_resource(
            router_id=router_id,
            ros_path="ip",
            item_id="settings",
            payload=req,
            request=mock_req,
            claims=superadmin_claims,
            db=mock_db,
        )
        assert res["ret"] == "ok"
        mock_client.post.assert_awaited_once_with("ip/settings/set", {"ip-forward": True})
        mock_l2_audit2.assert_awaited_once()


# ==============================================================================
# 4. PRUEBAS DE ELIMINACIÓN DE CONEXIONES EN FIREWALL CONNTRACK
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_firewall_connection_success(superadmin_claims, mock_db):
    """Verifica la eliminación de una conexión de firewall conntrack."""
    router_id = uuid.uuid4()
    conn_id = "*4A"

    with patch("src.api.v1.webfig_firewall.get_router_and_client", new_callable=AsyncMock) as mock_get_rc:
        mock_client = AsyncMock()
        mock_client.delete.return_value = {}
        mock_get_rc.return_value = (SimpleNamespace(id=router_id), mock_client)

        res = await delete_firewall_connection(
            router_id=router_id,
            conn_id=conn_id,
            proto="ipv4",
            claims=superadmin_claims,
            db=mock_db,
        )
        assert res == {}
        mock_client.delete.assert_awaited_once_with(f"/ip/firewall/connection/{conn_id}")
