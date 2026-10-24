# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para WebFig Capa 1: Interfaces, SFP DDM, IP, Anti-Suicidio, Firewall, Routing, PPP, Queues, System y Tools."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
)
from src.api.v1.webfig_firewall import (
    _build_firewall_patch_data,
    _check_input_chain_permission,
    _validate_firewall_params,
)
from src.api.v1.webfig_interfaces import (
    _calculate_optical_health,
    _parse_sfp_diagnostics,
)
from src.api.v1.webfig_ip import (
    _verify_anti_suicide_rule,
)
from src.api.v1.webfig_ppp import (
    _sanitize_secrets,
)
from src.api.v1.webfig_routing import (
    _build_bgp_summary,
)
from src.api.v1.webfig_system_tools import (
    _build_user_patch_data,
    _check_disabling_api_user,
    _filter_schedulers,
)
from src.core.crypto import encrypt_aes_gcm
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterCredentialsVault
from src.schemas.webfig_firewall import FirewallRuleUpdateRequest
from src.schemas.webfig_ops import SystemUserUpdateRequest


@pytest.fixture
def test_router() -> Router:
    tenant_id = uuid.uuid4()
    r = Router(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        display_name="Core-01",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
        serial_number="SN111",
    )
    aad = f"{tenant_id}:{r.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"admin_pass", aad)
    r.vault = RouterCredentialsVault(
        router_id=r.id,
        tenant_id=tenant_id,
        api_username="rosgrid_api",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
    )
    return r


# ============================================================================
# WEBFIG COMMON TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_router_and_client(test_router: Router) -> None:
    db = AsyncMock()

    class MockResult:
        def scalar_one_or_none(self) -> Router:
            return test_router

    db.execute.return_value = MockResult()
    claims = {"tid": str(test_router.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    r_obj, client = await get_router_and_client(test_router.id, claims, db)
    assert r_obj.id == test_router.id
    assert client.username == "rosgrid_api"
    assert client.password == "admin_pass"


@pytest.mark.asyncio
async def test_get_router_and_client_auto_tofu(test_router: Router) -> None:
    db = AsyncMock()

    class MockResult:
        def scalar_one_or_none(self) -> Router:
            return test_router

    db.execute.return_value = MockResult()
    claims = {"tid": str(test_router.tenant_id), "sub": str(uuid.uuid4()), "rol": SystemRoleEnum.TENANT_ADMIN.value}

    fake_client = AsyncMock(spec=MikrotikRestClient)
    fake_client.ensure_ssl_verified = AsyncMock(return_value="cafebabe12345678")
    fake_client.username = "rosgrid_api"
    fake_client.password = "admin_pass"

    with patch("src.api.v1.webfig_common._create_client_from_vault", return_value=fake_client):
        r_obj, client = await get_router_and_client(test_router.id, claims, db)
        assert r_obj.ssl_trust_status.value == "TRUSTED_PINNED"
        assert r_obj.ssl_sha256_fingerprint == "cafebabe12345678"
        assert client.ssl_pinned_fingerprint == "cafebabe12345678"
        assert db.commit.await_count >= 1


@pytest.mark.asyncio
async def test_cached_mikrotik_get() -> None:
    fake_redis = AsyncMock()
    fake_redis.get.return_value = None
    client = AsyncMock()
    client.get.return_value = [{"name": "ether1"}]
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    res = await cached_mikrotik_get(
        redis=fake_redis,
        tenant_id=t_id,
        router_id=r_id,
        endpoint="/interface",
        client=client,
        ttl_seconds=30,
    )
    assert res == [{"name": "ether1"}]
    fake_redis.setex.assert_awaited_once()

    # Second call hits cache
    fake_redis.get.return_value = '[{"name": "ether1"}]'
    res_cached = await cached_mikrotik_get(
        redis=fake_redis,
        tenant_id=t_id,
        router_id=r_id,
        endpoint="/interface",
        client=client,
    )
    assert res_cached == [{"name": "ether1"}]


@pytest.mark.asyncio
async def test_execute_safe_mutation() -> None:
    client = AsyncMock()
    coro_called = False

    async def sample_coro() -> str:
        nonlocal coro_called
        coro_called = True
        return "SUCCESS"

    with patch("src.api.v1.webfig_common.execute_with_safemode", return_value="SAFE_SUCCESS"):
        res = await execute_safe_mutation(
            client=client,
            menu="/ip/address",
            action="set",
            item_id="*1",
            before_state={".id": "*1"},
            coro_fn=sample_coro,
        )
        assert res == "SAFE_SUCCESS"


# ============================================================================
# INTERFACES & SFP DDM TESTS (Boundary testing)
# ============================================================================


def test_classify_sfp_health_boundaries() -> None:
    # >= -20.0 is OPTIMAL
    assert _calculate_optical_health(-20.0) == "OPTIMAL"
    assert _calculate_optical_health(-15.5) == "OPTIMAL"

    # < -20.0 and >= -25.0 is WARNING
    assert _calculate_optical_health(-20.01) == "WARNING"
    assert _calculate_optical_health(-25.0) == "WARNING"

    # < -25.0 is CRITICAL_LOW_LIGHT
    assert _calculate_optical_health(-25.01) == "CRITICAL_LOW_LIGHT"
    assert _calculate_optical_health(-30.0) == "CRITICAL_LOW_LIGHT"

    # None is OPTIMAL
    assert _calculate_optical_health(None) == "OPTIMAL"


def test_parse_sfp_diagnostics() -> None:
    raw = {
        "sfp-temperature": "42",
        "sfp-supply-voltage": "3.31",
        "sfp-tx-bias-current": "18",
        "sfp-tx-power": "-3.12",
        "sfp-rx-power": "-6.45",
        "sfp-wavelength": "1310",
        "sfp-vendor-name": "MikroTik",
        "sfp-vendor-part-number": "S+31DLC10D",
    }
    diag = _parse_sfp_diagnostics("sfp1", raw)
    assert diag.sfp_temperature_c == 42.0
    assert diag.sfp_supply_voltage_v == 3.31
    assert diag.sfp_tx_bias_ma == 18.0
    assert diag.sfp_tx_power_dbm == -3.12
    assert diag.sfp_rx_power_dbm == -6.45
    assert diag.optical_health == "OPTIMAL"
    assert diag.sfp_wavelength_nm == 1310


# ============================================================================
# IP & ANTI-SUICIDE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_verify_anti_suicide_rule() -> None:
    from src.schemas.webfig_l1_net import IpServiceUpdateRequest

    client = AsyncMock()

    # Normal service change
    client.get.return_value = {"name": "api", "port": 8728}
    await _verify_anti_suicide_rule(
        client=client,
        item_id="*1",
        payload=IpServiceUpdateRequest(port=8728, disabled=False),
    )

    # Suicide: Disabling the exact port/service RoSGrid uses to connect (www-ssl)
    client.get.return_value = {"name": "www-ssl", "port": 443}
    with pytest.raises(HTTPException) as exc1:
        await _verify_anti_suicide_rule(
            client=client,
            item_id="*2",
            payload=IpServiceUpdateRequest(disabled=True),
        )
    assert exc1.value.status_code == 422
    assert "No puedes deshabilitar el servicio www-ssl" in exc1.value.detail

    # Suicide: Changing the port away from what www-ssl currently uses
    with pytest.raises(HTTPException) as exc2:
        await _verify_anti_suicide_rule(
            client=client,
            item_id="*2",
            payload=IpServiceUpdateRequest(port=8443),
        )
    assert exc2.value.status_code == 422


# ============================================================================
# FIREWALL TESTS
# ============================================================================


def test_validate_firewall_params() -> None:
    _validate_firewall_params("ip", "filter")
    _validate_firewall_params("ipv6", "nat")
    _validate_firewall_params("ip", "mangle")
    _validate_firewall_params("ip", "raw")

    with pytest.raises(HTTPException):
        _validate_firewall_params("ip", "invalid_table")
    with pytest.raises(HTTPException):
        _validate_firewall_params("invalid_proto", "filter")


def test_check_input_chain_permission() -> None:
    # Non-input chain allows lower roles
    _check_input_chain_permission("forward", SystemRoleEnum.SUPPORT_L2.value)

    # Input chain requires L3 or higher
    _check_input_chain_permission("input", SystemRoleEnum.SUPPORT_L3.value)
    _check_input_chain_permission("input", SystemRoleEnum.TENANT_ADMIN.value)

    with pytest.raises(HTTPException) as exc:
        _check_input_chain_permission("input", SystemRoleEnum.SUPPORT_L2.value)
    assert exc.value.status_code == 403


def test_build_firewall_patch_data() -> None:
    payload = FirewallRuleUpdateRequest(
        chain="forward",
        action="accept",
        src_address="192.168.1.0/24",
        comment="Allow LAN",
        disabled=False,
    )
    data = _build_firewall_patch_data(payload)
    assert data["chain"] == "forward"
    assert data["action"] == "accept"
    assert data["src-address"] == "192.168.1.0/24"
    assert data["comment"] == "Allow LAN"
    assert data["disabled"] is False


# ============================================================================
# ROUTING & BGP TESTS
# ============================================================================


def test_build_bgp_summary() -> None:
    raw_sessions = [
        {"name": "peer1", "established": "true", "remote.address": "1.1.1.1", "remote.as": 65001, "local.as": 65000},
        {"name": "peer2", "established": "false", "remote.address": "2.2.2.2", "remote.as": 65002, "local.as": 65000},
        {"name": "peer3", "established": "true", "remote.address": "3.3.3.3", "remote.as": 65003, "local.as": 65000},
    ]
    raw_connections: list[dict[str, Any]] = []
    summary = _build_bgp_summary(raw_sessions, raw_connections)
    assert summary.total_configured_connections == 0
    assert summary.established_sessions_count == 2
    assert len(summary.sessions) == 3


# ============================================================================
# PPP SECRET REDACTION TESTS
# ============================================================================


def test_sanitize_secrets() -> None:
    raw_secrets = [
        {"name": "user1", "password": "super_secret_password"},
        {"name": "user2", "password": "another_secret"},
    ]

    # Non-admin sees [REDACTED]
    sanitized = _sanitize_secrets(raw_secrets, SystemRoleEnum.SUPPORT_L2.value)
    assert sanitized[0]["password"] == "[REDACTED]"
    assert sanitized[1]["password"] == "[REDACTED]"

    # Admin sees actual passwords
    admin_view = _sanitize_secrets(raw_secrets, SystemRoleEnum.TENANT_ADMIN.value)
    assert admin_view[0]["password"] == "super_secret_password"


# ============================================================================
# SYSTEM & TOOLS TESTS
# ============================================================================


def test_filter_schedulers() -> None:
    raw = [
        {"name": "backup-daily", "interval": "1d"},
        {"name": "rosgrid-safemode-abc12345", "interval": "00:01:00"},
        {"name": "custom-script", "interval": "1h"},
    ]
    filtered = _filter_schedulers(raw)
    assert len(filtered) == 2
    assert all("safemode" not in s["name"] for s in filtered)


def test_check_disabling_api_user(test_router: Router) -> None:
    # Attempting to disable the rosgrid_api user should be rejected
    before_user = {"name": "rosgrid_api"}
    with pytest.raises(HTTPException) as exc:
        _check_disabling_api_user(test_router, before_user, disabled=True)
    assert exc.value.status_code == 422
    assert "No puedes deshabilitar el usuario API" in exc.value.detail

    # Disabling another user is allowed
    other_user = {"name": "john_doe"}
    _check_disabling_api_user(test_router, other_user, disabled=True)


def test_build_user_patch_data() -> None:
    payload = SystemUserUpdateRequest(
        group="full",
        comment="Admin User",
        disabled=False,
    )
    patch_data = _build_user_patch_data(payload)
    assert patch_data["group"] == "full"
    assert patch_data["comment"] == "Admin User"
    assert patch_data["disabled"] is False
