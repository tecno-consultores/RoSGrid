# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Hito 19: Alerta de Caída Masiva y Geolocalización de ONUs."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.api.v1.field_ops import certify_installation, detect_fiber_cuts_engine
from src.api.v1.subscribers import list_subscriber_devices
from src.models.core import SystemRoleEnum, Tenant
from src.models.ipam import (
    CustomerService,
    CustomerServiceStatusEnum,
    FieldInstallationOrder,
    FieldOrderStatusEnum,
    ONUModeEnum,
)
from src.schemas.field_ops import FieldCertifyOrderRequest


class MockDbResult:
    def __init__(self, items: list[object] | None = None) -> None:
        self._items = items or []

    def scalar_one_or_none(self) -> object | None:
        return self._items[0] if self._items else None

    def scalars(self) -> "MockDbResult":
        return self

    def all(self) -> list[object]:
        return self._items


@pytest.mark.asyncio
async def test_certify_installation_associates_gps_coordinates_to_subscriber() -> None:
    """Verifica que la certificación asocie las coordenadas GPS al equipo (Sub-tarea 19.3 / docs/specs/32 §6.2)."""
    db = AsyncMock()
    t_id = uuid.uuid4()
    ord_id = uuid.uuid4()
    svc_id = uuid.uuid4()

    claims = {
        "sub": str(uuid.uuid4()),
        "username": "tech_caracas",
        "rol": SystemRoleEnum.FIELD_TECH.value,
        "tid": str(t_id),
    }

    order = FieldInstallationOrder(
        id=ord_id,
        tenant_id=t_id,
        customer_service_id=svc_id,
        status=FieldOrderStatusEnum.ASSIGNED,
    )
    svc = CustomerService(
        id=svc_id,
        tenant_id=t_id,
        router_id=uuid.uuid4(),
        status=CustomerServiceStatusEnum.PENDING_INSTALL.value,
        onu_mode=ONUModeEnum.ROUTER,
    )

    db.execute.side_effect = [
        MockDbResult([order]),  # order found
        MockDbResult([svc]),  # customer service found
    ]

    payload = FieldCertifyOrderRequest(
        order_id=ord_id,
        onu_scanned_serial="ZTEGC99887766",
        onu_scanned_mac="48:8F:5A:11:22:33",
        tech_latitude=Decimal("10.480600"),
        tech_longitude=Decimal("-66.903600"),
        notes="Instalación certificada en poste 14",
    )

    with (
        patch("src.api.v1.field_ops.write_audit_log", AsyncMock()) as mock_audit,
        patch("src.api.v1.field_ops.publish_network_service_event", AsyncMock()) as mock_pub,
    ):
        result = await certify_installation(payload, db=db, claims=claims)
        assert result.status == FieldOrderStatusEnum.CERTIFIED
        assert svc.status == CustomerServiceStatusEnum.ACTIVE.value
        assert svc.onu_serial_number == "ZTEGC99887766"
        assert svc.latitude == Decimal("10.480600")
        assert svc.longitude == Decimal("-66.903600")
        mock_audit.assert_called_once()
        mock_pub.assert_called_once()


@pytest.mark.asyncio
async def test_detect_fiber_cuts_triggers_mass_outage_when_threshold_exceeded() -> None:
    """Verifica que si la cantidad de ONUs caídas supera mass_outage_threshold se emita MASS_OUTAGE_TRIGGERED (Sub-tarea 19.2)."""
    db = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    claims = {
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.NOC_MONITOR.value,
        "tid": str(t_id),
    }

    tenant = Tenant(id=t_id, slug="isp-alpha", name="ISP Alpha", mass_outage_threshold=8)

    db.execute.side_effect = [
        MockDbResult(items=[(r_id, "sfp-plus1", "NAP-NORTE", 12)]),  # 12 ONUs caídas (supera umbral 8)
        MockDbResult([tenant]),  # tenant con umbral = 8
        MockDbResult([]),  # no existe incidente previo
    ]

    mock_redis = AsyncMock()
    with (
        patch("src.api.v1.field_ops.write_audit_log", AsyncMock()) as mock_audit,
        patch("src.api.v1.field_ops.publish_network_service_event", AsyncMock()) as mock_net_pub,
        patch("src.api.v1.field_ops.get_redis_client", return_value=mock_redis),
    ):
        incidents = await detect_fiber_cuts_engine(threshold_onus=3, db=db, claims=claims)
        assert len(incidents) == 1
        assert incidents[0].affected_onus_count == 12

        # 1. Evento de red hacia webhooks salientes
        mock_net_pub.assert_called_once()
        call_args = mock_net_pub.call_args[1]
        assert call_args["event_name"] == "MASS_OUTAGE_TRIGGERED"
        assert call_args["payload"]["affected_onus_count"] == 12

        # 2. Evento WebSocket al Wallboard NOC
        mock_redis.publish.assert_called_once()

        # 3. Auditoría inmutable WORM con HMAC-SHA256 encadenado
        mock_audit.assert_called_once()
        audit_call = mock_audit.call_args[1]
        assert audit_call["event_action"] == "MASS_OUTAGE_TRIGGERED"
        assert audit_call["after_state"]["affected_onus_count"] == 12


@pytest.mark.asyncio
async def test_detect_fiber_cuts_does_not_trigger_mass_outage_when_below_threshold() -> None:
    """Verifica que caídas por debajo del umbral generen corte pero no caída masiva."""
    db = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    claims = {
        "sub": str(uuid.uuid4()),
        "username": "noc_operator",
        "rol": SystemRoleEnum.NOC_MONITOR.value,
        "tid": str(t_id),
    }

    tenant = Tenant(id=t_id, slug="isp-alpha", name="ISP Alpha", mass_outage_threshold=15)

    db.execute.side_effect = [
        MockDbResult(items=[(r_id, "sfp-plus1", "NAP-SUR", 6)]),  # 6 ONUs caídas (< 15)
        MockDbResult([tenant]),  # umbral = 15
        MockDbResult([]),  # nuevo incidente
    ]

    with (
        patch("src.api.v1.field_ops.write_audit_log", AsyncMock()) as mock_audit,
        patch("src.api.v1.field_ops.publish_network_service_event", AsyncMock()) as mock_net_pub,
    ):
        incidents = await detect_fiber_cuts_engine(threshold_onus=3, db=db, claims=claims)
        assert len(incidents) == 1
        assert incidents[0].affected_onus_count == 6

        # NO debe emitir alarma de caída masiva
        mock_net_pub.assert_not_called()
        mock_audit.assert_not_called()


@pytest.mark.asyncio
async def test_list_subscriber_devices_returns_gps_and_fields() -> None:
    """Verifica que el listado de ONUs para el mapa devuelva coordenadas y campos esperados."""
    db = AsyncMock()
    t_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.FIELD_TECH.value}

    dev = CustomerService(
        id=uuid.uuid4(),
        tenant_id=t_id,
        router_id=uuid.uuid4(),
        status="ACTIVE",
        onu_mode=ONUModeEnum.ROUTER,
        onu_serial_number="ZTEGC11223344",
        latitude=Decimal("10.480600"),
        longitude=Decimal("-66.903600"),
        last_reachability_status="ONLINE",
    )

    db.execute.return_value = MockDbResult([dev])
    devices = await list_subscriber_devices(db=db, claims=claims)
    assert len(devices) == 1
    assert devices[0].onu_serial_number == "ZTEGC11223344"
    assert devices[0].latitude == Decimal("10.480600")
