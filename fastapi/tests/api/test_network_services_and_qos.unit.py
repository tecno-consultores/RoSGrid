# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para aprovisionamiento técnico idempotente de servicios de red y webhooks salientes (Hito 17)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.network_services import (
    _get_tenant_id,
    _resolve_subscriber_target_ip,
    _validate_idempotency_key,
    change_network_service_rate_limit,
    get_network_service_detail,
    isolate_network_service,
    restore_network_service,
)
from src.models.core import SystemRoleEnum
from src.models.ipam import (
    BandwidthProfile,
    IPAMAddress,
    SubscriberDevice,
)
from src.schemas.network_services import ChangeRateLimitRequest
from src.services.network_events import (
    publish_network_service_event,
    send_signed_webhook_payload,
)


class MockDbScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


class MockDbResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None):
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single if single is not None else (items[0] if items else None)

    def scalars(self) -> MockDbScalars:
        return MockDbScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single


# ============================================================================
# HELPER & VALIDATION TESTS
# ============================================================================


def test_validate_idempotency_key_valid_and_invalid() -> None:
    valid_uuid_str = str(uuid.uuid4())
    parsed = _validate_idempotency_key(valid_uuid_str)
    assert str(parsed) == valid_uuid_str

    with pytest.raises(HTTPException) as exc_invalid:
        _validate_idempotency_key("not-a-uuid")
    assert exc_invalid.value.status_code == 422

    with pytest.raises(HTTPException) as exc_none:
        _validate_idempotency_key(None)  # type: ignore[arg-type]
    assert exc_none.value.status_code == 422


def test_get_tenant_id_from_claims() -> None:
    t_id = uuid.uuid4()
    assert _get_tenant_id({"tid": str(t_id)}) == t_id
    assert _get_tenant_id({"tenant_id": str(t_id)}) == t_id

    with pytest.raises(HTTPException) as exc_missing:
        _get_tenant_id({})
    assert exc_missing.value.status_code == 401


@pytest.mark.asyncio
async def test_resolve_subscriber_target_ip() -> None:
    dev = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        router_id=uuid.uuid4(),
        endpoint_identifier="EP-TEST",
        assigned_ipv4="10.200.1.50",
    )
    ip1 = await _resolve_subscriber_target_ip(dev)
    assert ip1 == "10.200.1.50"

    dev.assigned_ipv4 = None
    ip_addr = MagicMock(spec=IPAMAddress)
    ip_addr.address = "10.200.1.60/32"
    dev.ipv4_address = ip_addr
    ip2 = await _resolve_subscriber_target_ip(dev)
    assert ip2 == "10.200.1.60"

    dev.ipv4_address = None
    ip3 = await _resolve_subscriber_target_ip(dev)
    assert ip3 is None


# ============================================================================
# GET DETAIL & ISOLATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_network_service_detail() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    s_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    # 1. 404 Not Found
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_nf:
        await get_network_service_detail(s_id, db=db, claims=claims)
    assert exc_nf.value.status_code == 404

    # 2. 200 Success
    dev = SubscriberDevice(
        id=s_id,
        tenant_id=t_id,
        router_id=uuid.uuid4(),
        endpoint_identifier="EP-ACTIVE-1",
        status="ACTIVE",
    )
    db.execute.return_value = MockDbResult([dev])
    res = await get_network_service_detail(s_id, db=db, claims=claims)
    assert res.id == s_id
    assert res.endpoint_identifier == "EP-ACTIVE-1"


@pytest.mark.asyncio
async def test_isolate_network_service_flow() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    s_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    valid_idem = str(uuid.uuid4())

    # 1. 404 Not Found
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_nf:
        await isolate_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
    assert exc_nf.value.status_code == 404

    # 2. ALREADY_ISOLATED (Idempotent 200)
    dev_isolated = SubscriberDevice(
        id=s_id,
        tenant_id=t_id,
        router_id=r_id,
        endpoint_identifier="EP-ISOLATED",
        status="ISOLATED_ADMINISTRATIVE",
    )
    db.execute.return_value = MockDbResult([dev_isolated])
    res_already = await isolate_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
    assert res_already.status == "ALREADY_ISOLATED"
    assert res_already.service_id == s_id

    # 3. Successful Isolation with RouterOS Mock and Events
    dev_active = SubscriberDevice(
        id=s_id,
        tenant_id=t_id,
        router_id=r_id,
        endpoint_identifier="EP-ACTIVE-2",
        assigned_ipv4="10.200.2.10",
        status="ACTIVE",
    )
    db.execute.return_value = MockDbResult([dev_active])

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        [],  # address-list check -> not found
        [{"name": "SUB_EP-ACTIVE-2", ".id": "*Q1"}],  # queue check -> found
    ]

    with (
        patch("src.api.v1.network_services.get_router_and_client", AsyncMock(return_value=(MagicMock(), mock_client))),
        patch("src.api.v1.network_services.write_audit_log", AsyncMock()),
        patch("src.api.v1.network_services.publish_network_service_event", AsyncMock()) as mock_pub,
    ):
        res_iso = await isolate_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
        assert res_iso.status == "ISOLATED"
        assert dev_active.status == "ISOLATED_ADMINISTRATIVE"
        mock_client.put.assert_awaited_once()
        mock_client.patch.assert_awaited_once_with(
            "/queue/simple/*Q1",
            {"max-limit": "64k/64k", "comment": "RoSGrid Aislado Preventivo (64k/64k)"},
        )
        mock_pub.assert_awaited_once()
        assert mock_pub.await_args.kwargs["event_name"] == "DEVICE_ISOLATED"

    # 4. Router failure fallback (does not crash DB update)
    dev_active.status = "ACTIVE"
    with (
        patch("src.api.v1.network_services.get_router_and_client", side_effect=Exception("Router offline")),
        patch("src.api.v1.network_services.write_audit_log", AsyncMock()),
        patch("src.api.v1.network_services.publish_network_service_event", AsyncMock()),
    ):
        res_fallback = await isolate_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
        assert res_fallback.status == "ISOLATED"
        assert dev_active.status == "ISOLATED_ADMINISTRATIVE"


# ============================================================================
# RESTORE & CHANGE RATE LIMIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_restore_network_service_flow() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    s_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    valid_idem = str(uuid.uuid4())

    # 1. 404 Not Found
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_nf:
        await restore_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
    assert exc_nf.value.status_code == 404

    # 2. ALREADY_ACTIVE (Idempotent 200)
    dev_active = SubscriberDevice(
        id=s_id,
        tenant_id=t_id,
        router_id=r_id,
        endpoint_identifier="EP-ACTIVE-RESTORE",
        status="ACTIVE",
    )
    db.execute.return_value = MockDbResult([dev_active])
    res_already = await restore_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
    assert res_already.status == "ALREADY_ACTIVE"
    assert res_already.service_id == s_id

    # 3. Successful Restoration with RouterOS Mock and Profile Rate Restoration
    prof = BandwidthProfile(
        id=uuid.uuid4(),
        tenant_id=t_id,
        name="100M-Corp",
        rate_down_kbps=100000,
        rate_up_kbps=50000,
        burst_down_kbps=120000,
        burst_up_kbps=60000,
        burst_threshold_down_kbps=80000,
        burst_threshold_up_kbps=40000,
        burst_time_seconds=8,
        priority=3,
        queue_type="pcq-download-default",
    )
    dev_isolated = SubscriberDevice(
        id=s_id,
        tenant_id=t_id,
        router_id=r_id,
        endpoint_identifier="EP-ISOLATED-3",
        assigned_ipv4="10.200.3.30",
        bandwidth_profile_id=prof.id,
        status="ISOLATED_ADMINISTRATIVE",
    )
    dev_isolated.bandwidth_profile = prof
    db.execute.return_value = MockDbResult([dev_isolated])

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        [{".id": "*ADDR1", "address": "10.200.3.30"}],  # address-list check -> found
        [{"name": "SUB_EP-ISOLATED-3", ".id": "*Q2"}],  # queue check -> found
    ]

    with (
        patch("src.api.v1.network_services.get_router_and_client", AsyncMock(return_value=(MagicMock(), mock_client))),
        patch("src.api.v1.network_services.write_audit_log", AsyncMock()),
        patch("src.api.v1.network_services.publish_network_service_event", AsyncMock()) as mock_pub,
    ):
        res_restored = await restore_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
        assert res_restored.status == "RESTORED"
        assert dev_isolated.status == "ACTIVE"
        mock_client.delete.assert_awaited_once_with("/ip/firewall/address-list/*ADDR1")
        mock_client.patch.assert_awaited_once_with(
            "/queue/simple/*Q2",
            {
                "max-limit": "50000k/100000k",
                "burst-limit": "60000k/120000k",
                "burst-threshold": "40000k/80000k",
                "burst-time": "8s/8s",
                "priority": "3/3",
                "comment": "RoSGrid Automated QoS",
            },
        )
        mock_pub.assert_awaited_once()
        assert mock_pub.await_args.kwargs["event_name"] == "DEVICE_RESTORED"

    # 4. Router failure fallback
    dev_isolated.status = "ISOLATED_ADMINISTRATIVE"
    with (
        patch(
            "src.api.v1.network_services.get_router_and_client", side_effect=Exception("Router communication failed")
        ),
        patch("src.api.v1.network_services.write_audit_log", AsyncMock()),
        patch("src.api.v1.network_services.publish_network_service_event", AsyncMock()),
    ):
        res_fb = await restore_network_service(s_id, idempotency_key=valid_idem, db=db, claims=claims)
        assert res_fb.status == "RESTORED"
        assert dev_isolated.status == "ACTIVE"


@pytest.mark.asyncio
async def test_change_network_service_rate_limit_flow() -> None:
    db = AsyncMock()
    t_id = uuid.uuid4()
    s_id = uuid.uuid4()
    r_id = uuid.uuid4()
    prof_id = uuid.uuid4()
    claims = {"tid": str(t_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}
    valid_idem = str(uuid.uuid4())
    req_payload = ChangeRateLimitRequest(bandwidth_profile_id=prof_id)

    # 1. 404 Service Not Found
    db.execute.return_value = MockDbResult([])
    with pytest.raises(HTTPException) as exc_s_nf:
        await change_network_service_rate_limit(s_id, req_payload, idempotency_key=valid_idem, db=db, claims=claims)
    assert exc_s_nf.value.status_code == 404

    # 2. 404 Profile Not Found
    dev = SubscriberDevice(
        id=s_id,
        tenant_id=t_id,
        router_id=r_id,
        endpoint_identifier="EP-QOS-1",
        status="ACTIVE",
    )
    db.execute.side_effect = [
        MockDbResult([dev]),  # device found
        MockDbResult([]),  # profile not found
    ]
    with pytest.raises(HTTPException) as exc_p_nf:
        await change_network_service_rate_limit(s_id, req_payload, idempotency_key=valid_idem, db=db, claims=claims)
    assert exc_p_nf.value.status_code == 404

    # 3. Success: Patch Queue on MikroTik
    prof = BandwidthProfile(
        id=prof_id,
        tenant_id=t_id,
        name="200M-Dedicated",
        rate_down_kbps=200000,
        rate_up_kbps=100000,
        burst_down_kbps=0,
        burst_up_kbps=0,
        burst_threshold_down_kbps=0,
        burst_threshold_up_kbps=0,
        burst_time_seconds=8,
        priority=1,
    )
    db.execute.side_effect = [
        MockDbResult([dev]),  # device found
        MockDbResult([prof]),  # profile found
    ]

    mock_client = AsyncMock()
    mock_client.get.return_value = [{"name": "SUB_EP-QOS-1", ".id": "*Q9"}]

    with (
        patch("src.api.v1.network_services.get_router_and_client", AsyncMock(return_value=(MagicMock(), mock_client))),
        patch("src.api.v1.network_services.write_audit_log", AsyncMock()),
    ):
        res = await change_network_service_rate_limit(
            s_id, req_payload, idempotency_key=valid_idem, db=db, claims=claims
        )
        assert res.status == "RATE_LIMIT_UPDATED"
        assert res.bandwidth_profile_name == "200M-Dedicated"
        assert res.rate_down_kbps == 200000
        assert res.rate_up_kbps == 100000
        assert dev.bandwidth_profile_id == prof_id
        mock_client.patch.assert_awaited_once_with(
            "/queue/simple/*Q9",
            {
                "max-limit": "100000k/200000k",
                "burst-limit": "0k/0k",
                "burst-threshold": "0k/0k",
                "burst-time": "8s/8s",
                "priority": "1/1",
            },
        )


# ============================================================================
# NETWORK EVENTS & OUTBOUND WEBHOOK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_publish_network_service_event() -> None:
    t_id = uuid.uuid4()
    mock_redis = AsyncMock()

    with patch("src.services.network_events.get_redis_client", return_value=mock_redis):
        await publish_network_service_event(
            tenant_id=t_id,
            event_name="DEVICE_ISOLATED",
            payload={"service_id": "svc-123"},
        )
        mock_redis.publish.assert_awaited_once()
        assert f"rg:pubsub:alerts:{t_id}" in mock_redis.publish.await_args[0][0]

    # Exception handling
    with patch("src.services.network_events.get_redis_client", side_effect=Exception("Redis dead")):
        # Should not raise
        await publish_network_service_event(t_id, "DEVICE_ISOLATED", {})


@pytest.mark.asyncio
async def test_send_signed_webhook_payload() -> None:
    webhook_url = "https://billing.isp.local/webhook"
    secret = "secret-token-key-123"

    mock_resp = MagicMock()
    mock_resp.is_success = True

    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)) as mock_post:
        success = await send_signed_webhook_payload(
            webhook_url=webhook_url,
            secret=secret,
            event_name="DEVICE_ISOLATED",
            payload={"status": "ISOLATED"},
        )
        assert success is True
        headers = mock_post.await_args.kwargs["headers"]
        assert "X-RoSGrid-Signature" in headers
        assert headers["X-RoSGrid-Signature"].startswith("sha256=")
        assert "X-RoSGrid-Signature-256" in headers

    # Error handling returns False
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        fail = await send_signed_webhook_payload(webhook_url, secret, "EVT", {})
        assert fail is False
