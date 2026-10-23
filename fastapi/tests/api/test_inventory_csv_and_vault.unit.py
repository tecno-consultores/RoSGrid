# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Inventario MikroTik, CSV Onboarding, Bóveda Criptográfica y Ventanas de Mantenimiento."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pyotp
import pytest
from fastapi import HTTPException

from src.api.v1.inventory_helpers import (
    apply_router_scalar_updates,
    build_router_from_csv,
    build_router_response,
    enrich_router_telemetry,
    perform_discovery,
    row_to_commit_item,
    validate_single_csv_row,
)
from src.core.crypto import decrypt_aes_gcm, encrypt_aes_gcm
from src.models.core import User
from src.models.inventory import (
    MaintenanceWindow,
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterNetworkRoleEnum,
    RouterTag,
    SSLTrustStatusEnum,
)
from src.schemas.inventory import (
    CreateRouterRequest,
    CsvCommitRowItem,
    UpdateRouterRequest,
    validate_router_target_url,
)


@pytest.fixture
def test_tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def test_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def test_router(test_tenant_id: uuid.UUID, test_user_id: uuid.UUID) -> Router:
    r = Router(
        id=uuid.uuid4(),
        tenant_id=test_tenant_id,
        display_name="Edge-Router-01",
        api_base_url="https://192.168.88.1:443",
        api_port=443,
        network_role=RouterNetworkRoleEnum.CORE,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="Datacenter Room 1",
        latitude=Decimal("10.4806"),
        longitude=Decimal("-66.9036"),
        online_since_date=date.today(),
        serial_number="SN123456789",
        is_reachable=True,
        ssl_trust_status=SSLTrustStatusEnum.TRUSTED_PINNED,
        ssl_sha256_fingerprint="a" * 64,
        created_by=test_user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    r.tags = [RouterTag(id=uuid.uuid4(), tenant_id=test_tenant_id, router_id=r.id, tag_name="core")]
    return r


@pytest.fixture
def test_vault(test_tenant_id: uuid.UUID, test_router: Router, test_user_id: uuid.UUID) -> RouterCredentialsVault:
    aad = f"{test_tenant_id}:{test_router.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"SecretPass123", aad)
    prev_ct, prev_iv, prev_tag = encrypt_aes_gcm(b"OldPass123", aad)
    vault = RouterCredentialsVault(
        router_id=test_router.id,
        tenant_id=test_tenant_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
        previous_password_ciphertext=prev_ct,
        previous_password_iv=prev_iv,
        previous_password_tag=prev_tag,
        auto_rotate_enabled=True,
        rotation_interval_days=30,
        updated_by=test_user_id,
    )
    test_router.vault = vault
    return vault


# ============================================================================
# INVENTORY HELPERS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_enrich_router_telemetry_online_and_offline() -> None:
    fake_pipeline = MagicMock()
    fake_pipeline.execute = AsyncMock(
        return_value=[{"state": "ONLINE", "cpu": "25", "last_free_memory_pct": "60"}, 1, 10]
    )
    fake_redis = MagicMock()
    fake_redis.pipeline.return_value = fake_pipeline

    res = await enrich_router_telemetry(fake_redis, uuid.uuid4(), uuid.uuid4())
    assert res["operational_status"] == "ONLINE"
    assert res["cpu_load_percent"] == 25
    assert res["memory_used_percent"] == 40
    assert res["syslog_active"] is True
    assert res["syslog_event_count"] == 10

    fake_pipeline.execute = AsyncMock(return_value=[{}, 0, 0])
    res_off = await enrich_router_telemetry(fake_redis, uuid.uuid4(), uuid.uuid4())
    assert res_off["operational_status"] == "OFFLINE"
    assert res_off["cpu_load_percent"] is None


@pytest.mark.asyncio
async def test_perform_discovery(test_router: Router) -> None:
    client = AsyncMock()
    client.ensure_ssl_verified.return_value = "b" * 64
    client.get.side_effect = [
        {"name": "DiscoveredIdentity"},
        {"version": "7.16.1", "board-name": "RB4011", "architecture-name": "arm64"},
        {"model": "RB4011iGS+", "current-firmware": "7.16.1", "serial-number": "SN987"},
    ]

    ok = await perform_discovery(client, test_router)
    assert ok is True
    assert test_router.is_reachable is True
    assert test_router.ros_identity == "DiscoveredIdentity"
    assert test_router.board_name == "RB4011"


def test_build_router_response(test_router: Router) -> None:
    telemetry = {"operational_status": "ONLINE", "cpu_load_percent": 15, "memory_used_percent": 30}
    resp = build_router_response(test_router, telemetry)
    assert resp.display_name == test_router.display_name
    assert resp.operational_status == "ONLINE"
    assert resp.tags == ["core"]


def test_apply_router_scalar_updates(test_router: Router) -> None:
    payload = UpdateRouterRequest(
        display_name=" New-Name ",
        latitude=Decimal("10.5"),
        longitude=Decimal("-66.9"),
    )
    apply_router_scalar_updates(test_router, payload)
    assert test_router.display_name == "New-Name"
    assert test_router.latitude == Decimal("10.5")
    assert test_router.longitude == Decimal("-66.9")


def test_validate_single_csv_row() -> None:
    existing = {"SN_EXISTING"}
    seen: set[str] = set()

    # Valid
    valid_row = {
        "display_name": "R1",
        "api_base_url": "https://10.0.0.1",
        "serial_number": "SN_NEW",
        "api_password": "pass",
    }
    is_valid, errors = validate_single_csv_row(valid_row, existing, seen)
    assert is_valid is True
    assert len(errors) == 0

    # Duplicate in seen
    is_valid2, errors2 = validate_single_csv_row(valid_row, existing, seen)
    assert is_valid2 is False
    assert any("duplicado" in e for e in errors2)

    # In existing
    bad_row = {
        "display_name": "R2",
        "api_base_url": "http://invalid",
        "serial_number": "SN_EXISTING",
        "api_password": "",
    }
    is_valid3, errors3 = validate_single_csv_row(bad_row, existing, seen)
    assert is_valid3 is False
    assert len(errors3) >= 3


def test_validate_single_csv_row_with_template_aliases() -> None:
    existing = {"SN_EXISTING"}
    seen: set[str] = set()

    # Fila generada a partir de la plantilla descargada en la UI
    template_row = {
        "display_name": "CCR2004-Edge-Norte",
        "ip_address": "192.168.10.1",
        "api_port": "8728",
        "ros_username": "api_admin",
        "ros_password": "ClaveSegura123!",
        "network_role": "EDGE_BGP",
        "serial_number": "HE4011ABC123",
        "latitude": "10.4806",
        "longitude": "-66.9036",
        "tags": "core;zona-norte",
    }
    is_valid, errors = validate_single_csv_row(template_row, existing, seen)
    assert is_valid is True
    assert len(errors) == 0

    # Conversión a CsvCommitRowItem
    item = row_to_commit_item(template_row)
    assert item.display_name == "CCR2004-Edge-Norte"
    assert item.api_base_url == "https://192.168.10.1"
    assert item.api_port == 8728
    assert item.api_username == "api_admin"
    assert item.api_password == "ClaveSegura123!"
    assert item.network_role == RouterNetworkRoleEnum.EDGE_BGP
    assert item.serial_number == "HE4011ABC123"
    assert item.latitude == Decimal("10.4806")
    assert item.tags == ["core", "zona-norte"]


def test_build_router_from_csv(test_tenant_id: uuid.UUID, test_user_id: uuid.UUID) -> None:
    item = CsvCommitRowItem(
        display_name="CSV-Router",
        api_base_url="https://10.10.10.1",
        api_port=443,
        network_role=RouterNetworkRoleEnum.DISTRIBUTION_SWITCH,
        admin_state=RouterAdminStateEnum.STAGING_LAB,
        physical_location="Rack 4",
        online_since_date=date.today(),
        serial_number="CSV-SN-123",
        api_username="admin",
        api_password="SuperSecretPassword",
        tags=["edge", "distribution"],
    )
    r, tags, vault = build_router_from_csv(item, test_tenant_id, test_user_id)
    assert r.display_name == "CSV-Router"
    assert len(tags) == 2
    assert vault.api_username == "admin"
    aad = f"{test_tenant_id}:{r.id}".encode()
    plain = decrypt_aes_gcm(
        vault.current_password_ciphertext,
        vault.current_password_iv,
        vault.current_password_tag,
        aad,
    ).decode("utf-8")
    assert plain == "SuperSecretPassword"


def test_validate_single_csv_row_with_custom_network_role() -> None:
    existing: set[str] = set()
    seen: set[str] = set()

    custom_row = {
        "display_name": "Switch-Distribucion-Piso2",
        "ip_address": "10.250.3.10",
        "api_port": "443",
        "ros_username": "admin",
        "ros_password": "Password123!",
        "network_role": "L1",
        "serial_number": "SN-L1-CUSTOM-001",
    }
    is_valid, errors = validate_single_csv_row(custom_row, existing, seen)
    assert is_valid is True
    assert len(errors) == 0

    item = row_to_commit_item(custom_row)
    assert item.display_name == "Switch-Distribucion-Piso2"
    assert item.network_role == "L1"
    assert item.serial_number == "SN-L1-CUSTOM-001"


def test_build_router_from_csv_with_custom_role(test_tenant_id: uuid.UUID, test_user_id: uuid.UUID) -> None:
    item = CsvCommitRowItem(
        display_name="Router-Custom-Role",
        api_base_url="https://10.250.3.11",
        api_port=443,
        network_role="L1",
        admin_state=RouterAdminStateEnum.PRODUCTION,
        physical_location="Nodo Secundario",
        online_since_date=date.today(),
        serial_number="SN-CUSTOM-L1-002",
        api_username="admin",
        api_password="StrongPassword123!",
    )
    r, tags, vault = build_router_from_csv(item, test_tenant_id, test_user_id)
    assert r.display_name == "Router-Custom-Role"
    assert r.network_role == "L1"
    assert vault.api_username == "admin"


def test_tenant_custom_role_model_metadata() -> None:
    from sqlalchemy import String
    from src.models.base import Base
    from src.models.inventory import TenantCustomRole

    # Validar registro en Base.metadata
    assert "tenant_custom_roles" in Base.metadata.tables
    table = Base.metadata.tables["tenant_custom_roles"]
    assert "tenant_id" in table.c
    assert "role_name" in table.c

    # Validar que routers.network_role es de tipo String en SQLAlchemy para admitir roles dinámicos
    routers_table = Base.metadata.tables["routers"]
    assert isinstance(routers_table.c.network_role.type, String)



# ============================================================================
# VAULT ENDPOINTS AND LOGIC
# ============================================================================


def test_generate_safe_ros_password() -> None:
    from src.api.v1.vault import _generate_safe_ros_password

    pwd = _generate_safe_ros_password(32)
    assert len(pwd) == 32
    # Ensure variety
    assert any(c.isupper() for c in pwd)
    assert any(c.islower() for c in pwd)


@pytest.mark.asyncio
async def test_decrypt_vault_passwords(
    test_tenant_id: uuid.UUID, test_router: Router, test_vault: RouterCredentialsVault
) -> None:
    from src.api.v1.vault import _decrypt_vault_passwords

    cur, prev = _decrypt_vault_passwords(test_vault, test_tenant_id, test_router.id)
    assert cur == "SecretPass123"
    assert prev == "OldPass123"


@pytest.mark.asyncio
async def test_verify_admin_totp(test_tenant_id: uuid.UUID) -> None:
    from src.api.v1.vault import _verify_admin_totp

    totp_secret = pyotp.random_base32()
    u = User(id=uuid.uuid4(), tenant_id=test_tenant_id, totp_enabled=True)
    aad = f"{test_tenant_id}:{u.id}".encode()
    ct, iv, tag = encrypt_aes_gcm(totp_secret.encode(), aad)
    u.totp_secret_ciphertext = ct
    u.totp_secret_iv = iv
    u.totp_secret_tag = tag

    db = AsyncMock()
    db.get.return_value = u

    # Valid code
    valid_code = pyotp.TOTP(totp_secret).now()
    user_res = await _verify_admin_totp(db, test_tenant_id, u.id, valid_code)
    assert user_res.id == u.id

    # Invalid code
    with pytest.raises(HTTPException) as exc_info:
        await _verify_admin_totp(db, test_tenant_id, u.id, "000000")
    assert exc_info.value.status_code == 401

    # User missing TOTP
    u.totp_enabled = False
    with pytest.raises(HTTPException) as exc_info2:
        await _verify_admin_totp(db, test_tenant_id, u.id, valid_code)
    assert exc_info2.value.status_code == 400


def test_maintenance_window_filters(test_router: Router) -> None:
    from sqlalchemy import select

    from src.api.v1.maintenance import _apply_window_filters

    q = select(MaintenanceWindow)
    filtered_q = _apply_window_filters(q, router_id=test_router.id, is_active=True, is_cancelled=False)
    assert filtered_q is not None

    filtered_inactive = _apply_window_filters(q, router_id=test_router.id, is_active=False, is_cancelled=True)
    assert filtered_inactive is not None


def test_ssrf_validation_rejects_loopback_and_metadata() -> None:
    blocked_urls = [
        "https://127.0.0.1:443",
        "https://127.0.1.1",
        "https://localhost:8443",
        "https://169.254.169.254/latest/meta-data",
        "https://rosgrid-db:5432",
        "https://rosgrid-redis:6379",
        "https://internal-service.local",
    ]
    for url in blocked_urls:
        with pytest.raises(ValueError, match="no permitid"):
            validate_router_target_url(url)

    # Valid external and telecommunications IPs should pass
    allowed_urls = [
        "https://10.0.0.1:443",
        "https://192.168.88.1:443",
        "https://172.16.50.1",
        "https://200.1.1.1:443",
        "https://router.empresa.com:8443",
    ]
    for url in allowed_urls:
        assert validate_router_target_url(url) == url

    # Verify CreateRouterRequest schema enforces it via field validator
    today = date.today()
    with pytest.raises(ValueError, match="no permitid"):
        CreateRouterRequest(
            display_name="R-Blocked",
            api_base_url="https://127.0.0.1:443",
            api_port=443,
            api_username="admin",
            api_password="pwd",
            network_role="EDGE",
            physical_location="NOC",
            online_since_date=today,
            serial_number="SN-TEST",
        )


def test_csv_row_ssrf_validation() -> None:
    existing: set[str] = set()
    seen: set[str] = set()

    # CSV row apuntando a metadata cloud (169.254.169.254)
    ssrf_row = {
        "display_name": "R-SSRF",
        "api_base_url": "https://169.254.169.254/latest/meta-data",
        "serial_number": "SN_SSRF_TEST",
        "api_password": "valid_password",
    }
    is_valid, errors = validate_single_csv_row(ssrf_row, existing, seen)
    assert is_valid is False
    assert any("link-local" in e or "no permitid" in e for e in errors)


@pytest.mark.asyncio
async def test_download_inventory_csv_template_endpoint() -> None:
    from src.api.v1.inventory import download_inventory_csv_template

    response = await download_inventory_csv_template()
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == 'attachment; filename="rosgrid-inventario-plantilla.csv"'
    assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
    decoded_body = response.body.decode("utf-8-sig")
    assert "display_name,ip_address,api_port" in decoded_body
    assert "CCR2004-Edge-Norte" in decoded_body
    assert "RB5009-Tower-Sur" in decoded_body
