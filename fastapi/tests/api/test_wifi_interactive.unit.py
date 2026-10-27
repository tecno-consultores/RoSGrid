# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Tests unitarios para la consola interactiva WiFi CAPsMAN v7 y endpoints de aprovisionamiento (Hito 27.13 / Spec 51)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.wifi import (
    create_capsman_configuration,
    create_provisioning_rule,
    create_security_profile,
    delete_capsman_configuration,
    delete_provisioning_rule,
    delete_security_profile,
    delete_wifi_client,
    list_capsman_ssids,
    list_provisioning_rules,
    list_security_profiles,
    quick_setup_wifi,
    reprovision_capsman_fleet,
    toggle_capsman_manager,
    update_capsman_configuration,
)
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.schemas.enterprise import (
    CapsmanToggleRequest,
    WifiConfigurationCreate,
    WifiConfigurationUpdate,
    WifiProvisioningRuleCreate,
    WifiQuickSetupRequest,
    WifiSecurityProfileCreate,
)


@pytest.fixture
def sample_claims() -> dict:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(uuid.uuid4()),
        "roles": [SystemRoleEnum.SUPERADMIN_GLOBAL.value],
        "permissions": ["*"],
    }


@pytest.fixture
def mock_router(sample_claims: dict) -> Router:
    r = Router()
    r.id = uuid.uuid4()
    r.tenant_id = uuid.UUID(sample_claims["tid"])
    r.display_name = "Core-Router-CAPsMAN"
    r.management_ip = "192.168.88.1"
    r.ros_version = "7.15"
    r.is_reachable = True
    return r


@pytest.fixture
def mock_db(mock_router: Router) -> AsyncMock:
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_router
    db.execute.return_value = mock_res
    return db


@pytest.fixture
def mock_db_not_found() -> AsyncMock:
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res
    return db


@pytest.mark.asyncio
async def test_capsman_toggle_manager_modern_and_legacy(
    sample_claims: dict, mock_router: Router, mock_db: AsyncMock
) -> None:
    """Verifica conmutación de estado del manager CAPsMAN bajo driver moderno v7 y legado."""
    fake_client_modern = AsyncMock()
    fake_client_modern.get = AsyncMock(return_value={"enabled": "false"})
    fake_client_modern.post = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_client_modern)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "ok"})),
    ):
        req_on = CapsmanToggleRequest(enabled=True, require_peer_certificate=False, auto_certificates=True)
        res_on = await toggle_capsman_manager(
            router_id=mock_router.id,
            payload=req_on,
            db=mock_db,
            claims=sample_claims,
        )
        assert res_on.manager_enabled is True
        assert res_on.driver == "wifi"
        assert "activado exitosamente" in res_on.message

        req_off = CapsmanToggleRequest(enabled=False)
        res_off = await toggle_capsman_manager(
            router_id=mock_router.id,
            payload=req_off,
            db=mock_db,
            claims=sample_claims,
        )
        assert res_off.manager_enabled is False

    # Fallback a driver legado
    fake_client_legacy = AsyncMock()
    fake_client_legacy.get = AsyncMock(side_effect=Exception("No such path"))
    fake_client_legacy.post = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_client_legacy)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "ok"})),
    ):
        res_legacy = await toggle_capsman_manager(
            router_id=mock_router.id,
            payload=req_on,
            db=mock_db,
            claims=sample_claims,
        )
        assert res_legacy.manager_enabled is True
        assert res_legacy.driver == "caps-man"


@pytest.mark.asyncio
async def test_security_profiles_crud_modern_and_legacy(
    sample_claims: dict, mock_router: Router, mock_db: AsyncMock
) -> None:
    """Verifica listar, crear con validación y eliminar perfiles de seguridad Wi-Fi (moderno y legado)."""
    fake_client = AsyncMock()
    fake_client.get = AsyncMock(
        return_value=[
            {
                ".id": "*1",
                "name": "sec-corporate",
                "authentication-types": "wpa2-psk,wpa3-psk",
                "passphrase": "secretpassphrase",
                "wps": "disable",
                "ft": "yes",
                "comment": "Corp Profile",
            }
        ]
    )
    fake_client.put = AsyncMock(return_value={"ret": "*2"})
    fake_client.delete = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_client)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "*2"})),
    ):
        sec_list = await list_security_profiles(
            router_id=mock_router.id,
            db=mock_db,
            claims=sample_claims,
        )
        assert len(sec_list) == 1
        assert sec_list[0].name == "sec-corporate"

        # Validación clave corta (< 8)
        bad_req = WifiSecurityProfileCreate(name="sec-fail", passphrase="123")
        with pytest.raises(HTTPException) as exc_info:
            await create_security_profile(
                router_id=mock_router.id,
                payload=bad_req,
                db=mock_db,
                claims=sample_claims,
            )
        assert exc_info.value.status_code == 422

        # Crear perfil válido en modo moderno
        good_req = WifiSecurityProfileCreate(
            name="sec-branch-office",
            authentication_types=["wpa2-psk", "wpa3-psk"],
            passphrase="SuperSecureWpa3Key!",
            wps_disabled=True,
            ft_enabled=True,
            comment="Branch Office",
        )
        created_profile = await create_security_profile(
            router_id=mock_router.id,
            payload=good_req,
            db=mock_db,
            claims=sample_claims,
        )
        assert created_profile.name == "sec-branch-office"

        # Eliminar perfil en modo moderno
        await delete_security_profile(
            router_id=mock_router.id,
            sec_id="*2",
            db=mock_db,
            claims=sample_claims,
        )

    # Crear perfil en modo legado
    fake_legacy_client = AsyncMock()
    fake_legacy_client.get = AsyncMock(side_effect=Exception("No modern wifi"))
    fake_legacy_client.put = AsyncMock(return_value={"ret": "*L2"})
    fake_legacy_client.delete = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_legacy_client)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "*L2"})),
    ):
        created_legacy = await create_security_profile(
            router_id=mock_router.id,
            payload=good_req,
            db=mock_db,
            claims=sample_claims,
        )
        assert created_legacy.name == "sec-branch-office"

        await delete_security_profile(
            router_id=mock_router.id,
            sec_id="*L2",
            db=mock_db,
            claims=sample_claims,
        )


@pytest.mark.asyncio
async def test_wifi_configurations_crud_modern_and_legacy(
    sample_claims: dict, mock_router: Router, mock_db: AsyncMock
) -> None:
    """Verifica creación con VLAN datapath, modificación PATCH y eliminación de SSID (moderno y legado)."""
    fake_client = AsyncMock()
    fake_client.get = AsyncMock(
        return_value=[
            {
                ".id": "*C1",
                "name": "cfg-corporate-hq",
                "ssid": "CorpNet-Secure",
                "security": "sec-corporate",
                "datapath.vlan-id": "50",
                "datapath.client-isolation": "yes",
                "disabled": "no",
                "hide-ssid": "no",
                "comment": "Main HQ WiFi",
            }
        ]
    )
    fake_client.put = AsyncMock(return_value={"ret": "*C1"})
    fake_client.patch = AsyncMock(return_value={"ret": "ok"})
    fake_client.delete = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_client)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "*C1"})),
    ):
        ssids = await list_capsman_ssids(
            router_id=mock_router.id,
            db=mock_db,
            claims=sample_claims,
        )
        assert len(ssids) == 1
        assert ssids[0].name == "cfg-corporate-hq"

        create_req = WifiConfigurationCreate(
            name="cfg-branch-secure",
            ssid="Branch-WiFi",
            security_profile="sec-corporate",
            vlan_id=60,
            client_isolation=True,
            comment="Branch Site",
        )
        created_cfg = await create_capsman_configuration(
            router_id=mock_router.id,
            payload=create_req,
            db=mock_db,
            claims=sample_claims,
        )
        assert created_cfg.name == "cfg-branch-secure"

        patch_req = WifiConfigurationUpdate(
            ssid="Branch-WiFi-Ultra",
            disabled=True,
            security_profile="sec-alt",
            vlan_id=70,
            client_isolation=False,
            hide_ssid=True,
            comment="Updated Comment",
        )
        res_patch = await update_capsman_configuration(
            router_id=mock_router.id,
            cfg_id="*C1",
            payload=patch_req,
            db=mock_db,
            claims=sample_claims,
        )
        assert res_patch["status"] == "ok"

        await delete_capsman_configuration(
            router_id=mock_router.id,
            cfg_id="*C1",
            db=mock_db,
            claims=sample_claims,
        )

    # Modo legado
    fake_legacy = AsyncMock()
    fake_legacy.get = AsyncMock(side_effect=Exception("No modern"))
    fake_legacy.put = AsyncMock(return_value={"ret": "*CL1"})
    fake_legacy.patch = AsyncMock(return_value={"ret": "ok"})
    fake_legacy.delete = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_legacy)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "*CL1"})),
    ):
        created_leg = await create_capsman_configuration(
            router_id=mock_router.id,
            payload=create_req,
            db=mock_db,
            claims=sample_claims,
        )
        assert created_leg.name == "cfg-branch-secure"

        await update_capsman_configuration(
            router_id=mock_router.id,
            cfg_id="*CL1",
            payload=patch_req,
            db=mock_db,
            claims=sample_claims,
        )
        await delete_capsman_configuration(
            router_id=mock_router.id,
            cfg_id="*CL1",
            db=mock_db,
            claims=sample_claims,
        )


@pytest.mark.asyncio
async def test_provisioning_rules_and_reprovision_modern_and_legacy(
    sample_claims: dict, mock_router: Router, mock_db: AsyncMock
) -> None:
    """Verifica reglas de aprovisionamiento y reprovisionamiento de flota (moderno y legado)."""
    fake_client = AsyncMock()

    async def fake_get(path, *args, **kwargs):
        if "provisioning" in path:
            return [
                {
                    ".id": "*P1",
                    "name": "prov-all-bands",
                    "action": "create-dynamic-enabled",
                    "master-configuration": "cfg-corporate-hq",
                    "slave-configurations": "cfg-guest",
                    "supported-bands": "2ghz-ax,5ghz-ax",
                    "identity-regex": ".*",
                }
            ]
        if "radio" in path or "remote-cap" in path:
            return [
                {".id": "*R1", "name": "cap-wifi1"},
                {".id": "*R2", "name": "cap-wifi2"},
            ]
        return []

    fake_client.get = AsyncMock(side_effect=fake_get)
    fake_client.put = AsyncMock(return_value={"ret": "*P2"})
    fake_client.post = AsyncMock(return_value={"ret": "ok"})
    fake_client.delete = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_client)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "*P2"})),
    ):
        rules = await list_provisioning_rules(
            router_id=mock_router.id,
            db=mock_db,
            claims=sample_claims,
        )
        assert len(rules) == 1

        create_rule = WifiProvisioningRuleCreate(
            name="prov-guests",
            action="create-dynamic-enabled",
            master_configuration="cfg-corporate-hq",
            slave_configurations=["cfg-guest"],
            supported_bands=["2ghz-ax", "5ghz-ax", "6ghz-ax"],
            comment="Guest APs Rule",
        )
        created_rule = await create_provisioning_rule(
            router_id=mock_router.id,
            payload=create_rule,
            db=mock_db,
            claims=sample_claims,
        )
        assert created_rule.name == "prov-guests"

        reprov_res = await reprovision_capsman_fleet(
            router_id=mock_router.id,
            db=mock_db,
            claims=sample_claims,
        )
        assert reprov_res.success is True

        await delete_provisioning_rule(
            router_id=mock_router.id,
            prov_id="*P2",
            db=mock_db,
            claims=sample_claims,
        )

    # Modo legado
    fake_leg = AsyncMock()
    fake_leg.get = AsyncMock(side_effect=[Exception("No modern"), [{".id": "*RC1"}]])
    fake_leg.put = AsyncMock(return_value={"ret": "*PL1"})
    fake_leg.post = AsyncMock(return_value={"ret": "ok"})
    fake_leg.delete = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_leg)),
        patch("src.api.v1.wifi.execute_safe_mutation", AsyncMock(return_value={"ret": "*PL1"})),
    ):
        created_leg_rule = await create_provisioning_rule(
            router_id=mock_router.id,
            payload=create_rule,
            db=mock_db,
            claims=sample_claims,
        )
        assert created_leg_rule.name == "prov-guests"

        await delete_provisioning_rule(
            router_id=mock_router.id,
            prov_id="*PL1",
            db=mock_db,
            claims=sample_claims,
        )


@pytest.mark.asyncio
async def test_kick_client_and_quick_setup_wizard_modern_and_legacy(
    sample_claims: dict, mock_router: Router, mock_db: AsyncMock
) -> None:
    """Verifica expulsión de clientes y Asistente Quick Setup (moderno y legado)."""
    fake_client = AsyncMock()
    fake_client.get = AsyncMock(return_value={"enabled": "true"})
    fake_client.delete = AsyncMock(return_value={"ret": "ok"})
    fake_client.put = AsyncMock(return_value={"ret": "ok"})
    fake_client.post = AsyncMock(return_value={"ret": "ok"})

    async def fake_mut_runner(*args, **kwargs):
        coro = kwargs.get("coro_fn")
        if coro:
            await coro()
        return {"ret": "ok"}

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_client)),
        patch("src.api.v1.wifi.execute_safe_mutation", side_effect=fake_mut_runner),
    ):
        # Kick client (modo moderno)
        await delete_wifi_client(
            router_id=mock_router.id,
            client_id="*REG12",
            db=mock_db,
            claims=sample_claims,
        )

        # Quick Setup Wizard (moderno)
        good_wiz = WifiQuickSetupRequest(
            corporate_ssid="RoSGrid-Corporate",
            corporate_passphrase="ComplexCorporatePassword123!",
            guest_ssid_enabled=True,
            guest_ssid="RoSGrid-Guests",
            guest_passphrase="GuestPassword123!",
            guest_vlan_id=200,
        )
        wiz_res = await quick_setup_wifi(
            router_id=mock_router.id,
            payload=good_wiz,
            db=mock_db,
            claims=sample_claims,
        )
        assert wiz_res.corporate_ssid == "RoSGrid-Corporate"

    # Kick client fallback a legacy registration-table
    fake_kick_leg = AsyncMock()
    fake_kick_leg.delete = AsyncMock(side_effect=[Exception("Modern not found"), {"ret": "ok"}])
    with patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_kick_leg)):
        await delete_wifi_client(
            router_id=mock_router.id,
            client_id="*REG12",
            db=mock_db,
            claims=sample_claims,
        )

    # Quick Setup Wizard en modo legado
    fake_wiz_leg = AsyncMock()
    fake_wiz_leg.get = AsyncMock(side_effect=Exception("No modern wifi"))
    fake_wiz_leg.post = AsyncMock(return_value={"ret": "ok"})
    fake_wiz_leg.put = AsyncMock(return_value={"ret": "ok"})

    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_wiz_leg)),
        patch("src.api.v1.wifi.execute_safe_mutation", side_effect=fake_mut_runner),
    ):
        wiz_leg_res = await quick_setup_wifi(
            router_id=mock_router.id,
            payload=good_wiz,
            db=mock_db,
            claims=sample_claims,
        )
        assert wiz_leg_res.corporate_ssid == "RoSGrid-Corporate"


@pytest.mark.asyncio
async def test_not_found_and_exception_branches(
    sample_claims: dict, mock_router: Router, mock_db_not_found: AsyncMock, mock_db: AsyncMock
) -> None:
    """Verifica manejo de errores 404 y 502 en todos los endpoints."""
    # 1. Router 404
    req_toggle = CapsmanToggleRequest(enabled=True)
    with pytest.raises(HTTPException) as exc_e:
        await toggle_capsman_manager(mock_router.id, req_toggle, mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await list_security_profiles(mock_router.id, mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await create_security_profile(
            mock_router.id,
            WifiSecurityProfileCreate(name="sec", passphrase="validpassphrase123"),
            mock_db_not_found,
            sample_claims,
        )
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await delete_security_profile(mock_router.id, "*1", mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await create_capsman_configuration(
            mock_router.id,
            WifiConfigurationCreate(name="cfg", ssid="ssid"),
            mock_db_not_found,
            sample_claims,
        )
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await update_capsman_configuration(
            mock_router.id, "*1", WifiConfigurationUpdate(ssid="s"), mock_db_not_found, sample_claims
        )
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await delete_capsman_configuration(mock_router.id, "*1", mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await list_provisioning_rules(mock_router.id, mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await create_provisioning_rule(
            mock_router.id,
            WifiProvisioningRuleCreate(name="pr", master_configuration="mc"),
            mock_db_not_found,
            sample_claims,
        )
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await delete_provisioning_rule(mock_router.id, "*1", mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await reprovision_capsman_fleet(mock_router.id, mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await delete_wifi_client(mock_router.id, "*1", mock_db_not_found, sample_claims)
    assert exc_e.value.status_code == 404

    with pytest.raises(HTTPException) as exc_e:
        await quick_setup_wifi(
            mock_router.id,
            WifiQuickSetupRequest(corporate_ssid="C", corporate_passphrase="validpassword123"),
            mock_db_not_found,
            sample_claims,
        )
    assert exc_e.value.status_code == 404

    # 2. Excepciones 502 al fallar ejecución de mutaciones
    fake_failing = AsyncMock()
    fake_failing.get = AsyncMock(side_effect=RuntimeError("Hardware connection lost"))
    with (
        patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_failing)),
        patch("src.api.v1.wifi.execute_safe_mutation", side_effect=RuntimeError("Crash")),
    ):
        with pytest.raises(HTTPException) as exc_e:
            await toggle_capsman_manager(mock_router.id, req_toggle, mock_db, sample_claims)
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await create_security_profile(
                mock_router.id,
                WifiSecurityProfileCreate(name="sec", passphrase="validpassphrase123"),
                mock_db,
                sample_claims,
            )
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await delete_security_profile(mock_router.id, "*1", mock_db, sample_claims)
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await create_capsman_configuration(
                mock_router.id,
                WifiConfigurationCreate(name="cfg", ssid="ssid"),
                mock_db,
                sample_claims,
            )
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await update_capsman_configuration(
                mock_router.id, "*1", WifiConfigurationUpdate(ssid="s"), mock_db, sample_claims
            )
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await delete_capsman_configuration(mock_router.id, "*1", mock_db, sample_claims)
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await create_provisioning_rule(
                mock_router.id,
                WifiProvisioningRuleCreate(name="pr", master_configuration="mc"),
                mock_db,
                sample_claims,
            )
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await delete_provisioning_rule(mock_router.id, "*1", mock_db, sample_claims)
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await quick_setup_wifi(
                mock_router.id,
                WifiQuickSetupRequest(corporate_ssid="C", corporate_passphrase="validpassword123"),
                mock_db,
                sample_claims,
            )
        assert exc_e.value.status_code == 502

    fake_failing_ctx = AsyncMock()
    fake_failing_ctx.__aenter__.side_effect = RuntimeError("Fatal socket error")
    with patch("src.api.v1.wifi.get_router_and_client", return_value=(mock_router, fake_failing_ctx)):
        with pytest.raises(HTTPException) as exc_e:
            await reprovision_capsman_fleet(mock_router.id, mock_db, sample_claims)
        assert exc_e.value.status_code == 502

        with pytest.raises(HTTPException) as exc_e:
            await delete_wifi_client(mock_router.id, "*1", mock_db, sample_claims)
        assert exc_e.value.status_code == 502
