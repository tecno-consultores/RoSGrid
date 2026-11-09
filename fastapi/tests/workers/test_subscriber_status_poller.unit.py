# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias para el Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller)."""

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import SubscriberDevice
from src.workers.subscriber_status_poller import (
    _clean_mac_hex,
    _extract_dhcp_lease_identifiers,
    _extract_ppp_active_identifiers,
    _is_device_matched,
    _is_router_cb_open,
    _parse_single_ping_packet,
    _poll_single_router_sessions,
    _probe_device_icmp_alive,
    _probe_devices_icmp,
    _publish_device_status_change,
    _run_single_poller_cycle,
    poll_tenant_subscribers_cycle,
    subscriber_status_poller_worker_loop,
)


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


@pytest.mark.asyncio
async def test_poller_isp_mode_falls_back_to_dhcp_leases_for_dhcp_subscribers(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que con is_isp_mode=True, si el abonado es DHCP y no está en /ppp/active, consulta /ip/dhcp-server/lease."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "OFFLINE"
    mock_device.pppoe_username = None
    mock_device.endpoint_identifier = "CLI-DHCP-01"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = [
        [],  # /ppp/active vacío
        [{"address": "192.168.10.50", "status": "bound", "mac-address": "48:8F:5A:11:22:33"}],  # /ip/dhcp-server/lease
    ]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=True)
            assert changed == 1
            assert mock_device.last_reachability_status == "ONLINE"


@pytest.mark.asyncio
async def test_poller_icmp_probe_marks_powered_off_dhcp_device_offline(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que cuando verify_icmp=True, si la ONU no responde Ping aunque el lease DHCP siga bound, pasa a OFFLINE."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "ONLINE"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = [
        {"address": "192.168.10.50", "status": "bound", "mac-address": "48:8F:5A:11:22:33"}
    ]
    mock_client.post.return_value = [{"sent": 1, "received": 0, "status": "timeout"}]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(
                mock_session,
                mock_tenant_id,
                mock_router,
                is_isp_mode=False,
                verify_icmp=True,
            )
            assert changed == 1
            assert mock_device.last_reachability_status == "OFFLINE"
            mock_redis.publish.assert_called_once()


@pytest.mark.asyncio
async def test_poller_icmp_probe_marks_phantom_pppoe_session_offline(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Spec 84: Si existe una sesión PPPoE fantasma en /ppp/active pero el ping ICMP falla, descarta pppoe_username y pasa a OFFLINE."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "ONLINE"
    mock_device.pppoe_username = "user001"
    mock_device.endpoint_identifier = "user001"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = [
        {"name": "user001", "address": "192.168.10.50", "caller-id": "48:8F:5A:11:22:33", "uptime": "2m16s"}
    ]
    mock_client.post.return_value = [{"sent": 1, "received": 0, "status": "timeout"}]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(
                mock_session,
                mock_tenant_id,
                mock_router,
                is_isp_mode=True,
                verify_icmp=True,
            )
            assert changed == 1
            assert mock_device.last_reachability_status == "OFFLINE"
            mock_redis.publish.assert_called_once()


def test_clean_mac_hex_helpers() -> None:
    assert _clean_mac_hex(None) == ""
    assert _clean_mac_hex("") == ""
    assert _clean_mac_hex("48:8F:5A-11:22:33") == "488F5A112233"
    assert _clean_mac_hex("---:;;") == ""


def test_extract_ppp_active_identifiers_variants() -> None:
    active: set[str] = set()
    _extract_ppp_active_identifiers(None, active)
    _extract_ppp_active_identifiers("not-a-list", active)
    _extract_ppp_active_identifiers(
        [
            "not-a-dict",
            {"name": "user01", "address": "10.0.0.1", "caller-id": "48:8F:5A:11:22:33"},
            {"name": "", "address": ""},
        ],
        active,
    )
    assert "user01" in active
    assert "10.0.0.1" in active
    assert "488F5A112233" in active


def test_extract_dhcp_lease_identifiers_variants() -> None:
    active: set[str] = set()
    _extract_dhcp_lease_identifiers(None, active)
    _extract_dhcp_lease_identifiers("not-a-list", active)
    _extract_dhcp_lease_identifiers(
        [
            "not-a-dict",
            {"status": "waiting", "address": "10.0.0.2"},
            {"status": "bound", "address": "10.0.0.2", "mac-address": "AA:BB:CC:DD:EE:FF"},
            {"status": "active", "active-address": "10.0.0.3", "active-mac-address": "11:22:33:44:55:66"},
        ],
        active,
    )
    assert "10.0.0.2" in active
    assert "AABBCCDDEEFF" in active
    assert "10.0.0.3" in active
    assert "112233445566" in active


def test_is_device_matched_variants(mock_device: SubscriberDevice) -> None:
    mock_device.assigned_ipv4 = "10.0.0.5"
    mock_device.onu_mac_address = "AABBCCDDEEFF"
    mock_device.pppoe_username = "testuser"

    assert _is_device_matched(mock_device, {"10.0.0.5"}) is True
    assert _is_device_matched(mock_device, {"AABBCCDDEEFF"}) is True
    assert _is_device_matched(mock_device, {"testuser"}) is True
    assert _is_device_matched(mock_device, {"other"}) is False

    mock_device.assigned_ipv4 = None
    mock_device.onu_mac_address = None
    mock_device.pppoe_username = None
    mock_device.endpoint_identifier = "EP-01"
    assert _is_device_matched(mock_device, {"ep-01"}) is True
    assert _is_device_matched(mock_device, set()) is False


def test_parse_single_ping_packet_variants() -> None:
    assert _parse_single_ping_packet({"received": "1"}) is True
    assert _parse_single_ping_packet({"received": 0, "status": "timeout"}) is False
    assert _parse_single_ping_packet({"status": "echo reply", "time": "2ms"}) is True
    assert _parse_single_ping_packet({"status": "host unreachable"}) is False
    assert _parse_single_ping_packet({"status": "net unreachable"}) is False
    assert _parse_single_ping_packet({"other": "field"}) is None


@pytest.mark.asyncio
async def test_probe_device_icmp_alive_branches() -> None:
    # Sin método post
    assert await _probe_device_icmp_alive(object(), "10.0.0.1") is None

    # Error en post
    mock_client_err = AsyncMock()
    mock_client_err.post.side_effect = RuntimeError("Socket closed")
    assert await _probe_device_icmp_alive(mock_client_err, "10.0.0.1") is None

    # Respuesta vacía o no list
    mock_client_empty = AsyncMock()
    mock_client_empty.post.return_value = []
    assert await _probe_device_icmp_alive(mock_client_empty, "10.0.0.1") is None

    # Éxito
    mock_client_ok = AsyncMock()
    mock_client_ok.post.return_value = [{"received": 1, "status": "echo reply", "time": "1ms"}]
    assert await _probe_device_icmp_alive(mock_client_ok, "10.0.0.1") is True

    # Lista con dicts no parseables
    mock_client_unparseable = AsyncMock()
    mock_client_unparseable.post.return_value = [{"dummy": "value"}]
    assert await _probe_device_icmp_alive(mock_client_unparseable, "10.0.0.1") is None


@pytest.mark.asyncio
async def test_probe_devices_icmp_updates_identifiers(mock_device: SubscriberDevice) -> None:
    mock_client = AsyncMock()
    mock_client.post.return_value = [{"received": 1, "time": "1ms"}]
    active: set[str] = set()

    mock_device.assigned_ipv4 = "10.0.0.10"
    mock_device.onu_mac_address = "AABBCCDDEEFF"
    await _probe_devices_icmp(mock_client, [mock_device], active)
    assert "10.0.0.10" in active

    # Dispositivo sin ip
    mock_device_no_ip = MagicMock(spec=SubscriberDevice)
    mock_device_no_ip.assigned_ipv4 = None
    await _probe_devices_icmp(mock_client, [mock_device_no_ip], active)

    # Dispositivo desconectado (icmp False)
    mock_client_dead = AsyncMock()
    mock_client_dead.post.return_value = [{"received": 0, "status": "timeout"}]
    await _probe_devices_icmp(mock_client_dead, [mock_device], active)
    assert "10.0.0.10" not in active
    assert "AABBCCDDEEFF" not in active


@pytest.mark.asyncio
async def test_publish_device_status_change_handles_redis_error(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    mock_redis = AsyncMock()
    mock_redis.publish.side_effect = ConnectionError("Redis down")
    # No debe propagar la excepción
    await _publish_device_status_change(
        mock_redis, mock_tenant_id, mock_router.id, mock_device, "ONLINE", datetime.now(UTC)
    )


@pytest.mark.asyncio
async def test_is_router_cb_open_variants(mock_tenant_id: uuid.UUID, mock_router: Router) -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"OPEN"
    assert await _is_router_cb_open(mock_redis, mock_tenant_id, mock_router.id) is True

    mock_redis.get.return_value = "CLOSED"
    assert await _is_router_cb_open(mock_redis, mock_tenant_id, mock_router.id) is False


@pytest.mark.asyncio
async def test_poll_single_router_sessions_client_creation_failure(
    mock_tenant_id: uuid.UUID, mock_router: Router
) -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", side_effect=ValueError("No vault")):
            res = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=False)
            assert res == 0


@pytest.mark.asyncio
async def test_poll_single_router_sessions_no_devices(
    mock_tenant_id: uuid.UUID, mock_router: Router
) -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=AsyncMock()):
            res = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=False)
            assert res == 0


@pytest.mark.asyncio
async def test_poll_single_router_sessions_client_error(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.side_effect = RuntimeError("REST API Timeout")

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            res = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=False)
            assert res == 0


@pytest.mark.asyncio
async def test_poll_tenant_subscribers_cycle_execution(
    mock_tenant_id: uuid.UUID, mock_router: Router
) -> None:
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Caso 1: sin routers
    mock_res_empty = MagicMock()
    mock_res_empty.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_res_empty

    with patch("src.workers.subscriber_status_poller.async_session_maker", return_value=mock_session):
        with patch("src.workers.subscriber_status_poller.set_tenant_context"):
            await poll_tenant_subscribers_cycle(mock_tenant_id, is_isp_mode=False)

    # Caso 2: con routers
    mock_res_routers = MagicMock()
    mock_res_routers.scalars.return_value.all.return_value = [mock_router]
    mock_session.execute.return_value = mock_res_routers

    with patch("src.workers.subscriber_status_poller.async_session_maker", return_value=mock_session):
        with patch("src.workers.subscriber_status_poller.set_tenant_context"):
            with patch("src.workers.subscriber_status_poller._poll_single_router_sessions") as mock_poll:
                with patch("asyncio.sleep"):
                    await poll_tenant_subscribers_cycle(mock_tenant_id, is_isp_mode=True)
                    mock_poll.assert_called_once()


@pytest.mark.asyncio
async def test_poller_isp_mode_handles_dhcp_get_exception(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "OFFLINE"
    mock_device.pppoe_username = None
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = [
        [],  # /ppp/active
        RuntimeError("DHCP lease error"),  # /ip/dhcp-server/lease throws
    ]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=True)
            assert changed == 0


@pytest.mark.asyncio
async def test_run_single_poller_cycle_and_worker_loop() -> None:
    mock_tenant = MagicMock()
    mock_tenant.id = uuid.uuid4()
    mock_tenant.name = "ISP Test"
    mock_tenant.isp_module_enabled = True

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [mock_tenant]
    mock_session.execute.return_value = mock_res

    with patch("src.workers.subscriber_status_poller.async_session_maker", return_value=mock_session):
        with patch("src.workers.subscriber_status_poller.set_tenant_context"):
            with patch("src.workers.subscriber_status_poller.poll_tenant_subscribers_cycle") as mock_cycle:
                # Caso éxito
                await _run_single_poller_cycle()
                mock_cycle.assert_called_once_with(mock_tenant.id, True)

                # Caso excepción atrapada en warning
                mock_cycle.side_effect = RuntimeError("Connection timeout")
                await _run_single_poller_cycle()

    # worker loop con excepción genérica seguida de CancelledError
    with patch(
        "src.workers.subscriber_status_poller._run_single_poller_cycle",
        side_effect=[RuntimeError("Temporary fault"), asyncio.CancelledError],
    ):
        with patch("asyncio.sleep"):
            await subscriber_status_poller_worker_loop()
