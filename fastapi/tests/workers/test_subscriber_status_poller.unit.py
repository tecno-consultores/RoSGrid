# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para el Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import SubscriberDevice
from src.workers.subscriber_status_poller import _poll_single_router_sessions


@pytest.fixture
def mock_tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_router(mock_tenant_id: uuid.UUID) -> Router:
    r = MagicMock(spec=Router)
    r.id = uuid.uuid4()
    r.tenant_id = mock_tenant_id
    r.display_name = "CCR2004-TEST"
    r.api_base_url = "https://10.0.0.1:443"
    r.admin_state = RouterAdminStateEnum.PRODUCTION
    r.is_reachable = True
    return r


@pytest.fixture
def mock_device(mock_tenant_id: uuid.UUID, mock_router: Router) -> SubscriberDevice:
    d = MagicMock(spec=SubscriberDevice)
    d.id = uuid.uuid4()
    d.tenant_id = mock_tenant_id
    d.router_id = mock_router.id
    d.endpoint_identifier = "CLIENTE-001"
    d.assigned_ipv4 = "192.168.10.50"
    d.onu_mac_address = "488F5A112233"
    d.pppoe_username = "user001"
    d.last_reachability_status = "ONLINE"
    d.last_seen_at = datetime.now(UTC)
    return d


@pytest.mark.asyncio
async def test_poller_skips_when_circuit_breaker_open(
    mock_tenant_id: uuid.UUID, mock_router: Router
) -> None:
    """Verifica que si el Circuit Breaker del router está abierto, el poller no intenta conectar."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = "OPEN"
    mock_session = AsyncMock()

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault") as mock_vault:
            res = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=False)
            assert res == 0
            mock_vault.assert_not_called()


@pytest.mark.asyncio
async def test_poller_zero_write_delta_filter_when_status_unchanged(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que si el dispositivo continúa en ONLINE, no se escribe en DB ni se emite Pub/Sub."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Circuit Breaker CLOSED
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    # Simulamos que /ip/dhcp-server/lease retorna el lease activo
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = [
        {"address": "192.168.10.50", "status": "bound", "mac-address": "48:8F:5A:11:22:33"}
    ]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=False)
            assert changed == 0
            mock_session.commit.assert_not_called()
            mock_redis.publish.assert_not_called()


@pytest.mark.asyncio
async def test_poller_detects_transition_and_publishes_event(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que ante una transición (ONLINE -> OFFLINE), persiste en DB y emite DEVICE_STATUS_CHANGED."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Circuit Breaker CLOSED
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "ONLINE"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    # Simulamos que la tabla de leases ya no contiene la IP del cliente (se desconectó)
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = []

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=False)
            assert changed == 1
            assert mock_device.last_reachability_status == "OFFLINE"
            mock_session.commit.assert_called_once()
            mock_redis.publish.assert_called_once()
            call_args = mock_redis.publish.call_args[0]
            assert "DEVICE_STATUS_CHANGED" in call_args[1]
            assert "OFFLINE" in call_args[1]


@pytest.mark.asyncio
async def test_poller_isp_mode_reads_ppp_active(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que en modo ISP consulta /ppp/active y reconoce al abonado por su nombre PPPoE."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "OFFLINE"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = [
        {"name": "user001", "address": "100.64.0.10", "uptime": "2h45m"}
    ]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=True)
            assert changed == 1
            assert mock_device.last_reachability_status == "ONLINE"
            mock_client.get.assert_called_once_with("/ppp/active")
            mock_session.commit.assert_called_once()
            mock_redis.publish.assert_called_once()
