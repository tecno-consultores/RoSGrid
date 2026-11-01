# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias Level-11X para Actualización Inteligente RouterOS v7 + Firmware y Auto-Detección CHR (Hito 28.1)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.api.v1.bulk_and_updates import (
    _DEFAULT_STARTER_TEMPLATES,
    _execute_single_router_upgrade,
    _is_chr_router,
    _probe_single_router_update,
    _run_router_template_steps,
    _should_skip_step_for_router,
)
from src.models.inventory import Router, RouterCredentialsVault
from src.schemas.bulk_and_updates import (
    RosUpdateExecuteRequest,
)


def test_starter_template_15_exists_and_schema() -> None:
    """Verifica que la plantilla #15 existe en _DEFAULT_STARTER_TEMPLATES con sus esquemas y parámetros."""
    tpl = next((t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "ACTUALIZACION_ROUTEROS_Y_FIRMWARE"), None)
    assert tpl is not None, "Plantilla ACTUALIZACION_ROUTEROS_Y_FIRMWARE debe estar presente en el catálogo"
    assert tpl["category"] == "SYSTEM"
    assert tpl["requires_safemode"] is False, "Las actualizaciones con reinicio de OS deben tener requires_safemode=False"

    var_keys = [v["key"] for v in tpl["variables_schema"]]
    assert "update_channel" in var_keys
    assert "upgrade_firmware" in var_keys

    endpoints = [s["endpoint"] for s in tpl["rest_steps_template"]]
    assert "system/package/update/set" in endpoints
    assert "system/package/update/check-for-updates" in endpoints
    assert "system/routerboard/settings/set" in endpoints
    assert "system/routerboard/upgrade" in endpoints
    assert "system/package/update/install" in endpoints


def test_is_chr_router_detection() -> None:
    """Verifica la detección determinística de CHR mediante board_name, model_name o routerboard=false."""
    chr_r1 = Router(board_name="CHR QEMU Standard PC (i440FX + PIIX, 1996)", model_name=None)
    assert _is_chr_router(chr_r1) is True

    chr_r2 = Router(board_name="x86_64", model_name="Cloud Hosted Router CHR")
    assert _is_chr_router(chr_r2) is True

    chr_r3 = Router(board_name="Unknown x86", model_name="Custom VM")
    assert _is_chr_router(chr_r3, rb_data={"routerboard": "false"}) is True
    assert _is_chr_router(chr_r3, rb_data={"routerboard": "no"}) is True

    rb_physical = Router(board_name="RB5009UG+S+", model_name="RB5009UG+S+")
    assert _is_chr_router(rb_physical, rb_data={"routerboard": "true"}) is False
    assert _is_chr_router(rb_physical) is False


def test_should_skip_step_for_router() -> None:
    """Verifica si un paso REST debe omitirse por ser comando de RouterBOOT en CHR o firmware desactivado."""
    pkg_step = {"endpoint": "system/package/update/set"}
    rb_step = {"endpoint": "system/routerboard/settings/set"}
    rb_upg_step = {"endpoint": "system/routerboard/upgrade"}

    # Pasos que no son routerboard nunca se omiten
    assert _should_skip_step_for_router(pkg_step, is_chr=True, vars_dict={}) is False
    assert _should_skip_step_for_router(pkg_step, is_chr=False, vars_dict={}) is False

    # Pasos de routerboard en CHR siempre se omiten
    assert _should_skip_step_for_router(rb_step, is_chr=True, vars_dict={"upgrade_firmware": "yes"}) is True
    assert _should_skip_step_for_router(rb_upg_step, is_chr=True, vars_dict={"upgrade_firmware": "yes"}) is True

    # Pasos de routerboard en equipo físico se ejecutan si upgrade_firmware == 'yes'
    assert _should_skip_step_for_router(rb_step, is_chr=False, vars_dict={"upgrade_firmware": "yes"}) is False
    assert _should_skip_step_for_router(rb_upg_step, is_chr=False, vars_dict={"upgrade_firmware": "yes"}) is False

    # Pasos de routerboard en equipo físico se omiten si upgrade_firmware == 'no'
    assert _should_skip_step_for_router(rb_step, is_chr=False, vars_dict={"upgrade_firmware": "no"}) is True
    assert _should_skip_step_for_router(rb_upg_step, is_chr=False, vars_dict={"upgrade_firmware": "no"}) is True


@pytest.mark.asyncio
async def test_run_router_template_steps_skips_routerboard_on_chr() -> None:
    """Verifica que sobre un CHR se omiten los pasos de RouterBOOT y se ejecutan solo los de RouterOS."""
    tpl = next(t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "ACTUALIZACION_ROUTEROS_Y_FIRMWARE")
    steps = [dict(s) for s in tpl["rest_steps_template"]]

    client = AsyncMock()
    client.post = AsyncMock(return_value={"status": "ok"})
    router_chr = Router(
        id=uuid.uuid4(),
        display_name="chr-edge-1",
        board_name="CHR QEMU Standard PC",
    )

    summary = await _run_router_template_steps(
        client=client,
        router_obj=router_chr,
        rendered_steps=steps,
        vars_dict={"upgrade_firmware": "yes", "update_channel": "stable"},
    )

    assert summary["is_chr"] is True
    assert summary["executed_steps"] == 3
    assert summary["skipped_steps"] == 2
    assert "CHR detectado" in summary["message"]
    # Se llamaron 3 endpoints
    assert client.post.call_count == 3


@pytest.mark.asyncio
async def test_run_router_template_steps_executes_all_on_routerboard() -> None:
    """Verifica que sobre un RouterBOARD físico se ejecutan los 5 pasos sin omitir ninguno."""
    tpl = next(t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "ACTUALIZACION_ROUTEROS_Y_FIRMWARE")
    steps = [dict(s) for s in tpl["rest_steps_template"]]

    client = AsyncMock()
    client.post = AsyncMock(return_value={"status": "ok"})
    router_rb = Router(
        id=uuid.uuid4(),
        display_name="rb-core-1",
        board_name="CCR2004-16G-2S+",
        model_name="CCR2004-16G-2S+",
    )

    summary = await _run_router_template_steps(
        client=client,
        router_obj=router_rb,
        rendered_steps=steps,
        vars_dict={"upgrade_firmware": "yes", "update_channel": "stable"},
    )

    assert summary["is_chr"] is False
    assert summary["executed_steps"] == 5
    assert summary["skipped_steps"] == 0
    assert "CHR detectado" not in summary["message"]
    assert client.post.call_count == 5


@pytest.mark.asyncio
async def test_probe_single_router_update_chr_vs_physical() -> None:
    """Verifica _probe_single_router_update para CHR y RouterBOARD físico con clientes REST simulados."""
    t_id = uuid.uuid4()
    vault = RouterCredentialsVault(
        api_username="admin",
        current_password_ciphertext=b"enc_data",
        current_password_iv=b"iv",
        current_password_tag=b"tag",
    )

    # Caso 1: CHR
    r_chr = Router(
        id=uuid.uuid4(),
        tenant_id=t_id,
        display_name="chr-1",
        board_name="CHR QEMU",
        ros_version="7.21.5 (long-term)",
        vault=vault,
    )

    mock_client_chr = AsyncMock()
    mock_client_chr.get = AsyncMock(
        side_effect=lambda ep: {
            "system/package/update": {
                "channel": "stable",
                "installed-version": "7.21.5",
                "latest-version": "7.24.2",
                "status": "New version is available",
            },
            "system/routerboard": {"routerboard": "false"},
        }.get(ep, {})
    )
    mock_client_chr.post = AsyncMock(return_value={})
    mock_client_chr.close = AsyncMock()

    with patch("src.api.v1.bulk_and_updates._create_client_from_vault", return_value=mock_client_chr):
        item_chr = await _probe_single_router_update(r_chr, "stable", t_id)
        assert item_chr.is_chr is True
        assert item_chr.action_plan == "CHR_OS_ONLY"
        assert item_chr.update_available is True
        assert item_chr.latest_version == "7.24.2"
        assert item_chr.current_firmware is None

    # Caso 2: RouterBOARD Físico
    r_rb = Router(
        id=uuid.uuid4(),
        tenant_id=t_id,
        display_name="rb5009-1",
        board_name="RB5009UG+S+",
        ros_version="7.15.3",
        vault=vault,
    )

    mock_client_rb = AsyncMock()
    mock_client_rb.get = AsyncMock(
        side_effect=lambda ep: {
            "system/package/update": {
                "channel": "stable",
                "installed-version": "7.15.3",
                "latest-version": "7.16.2",
                "status": "New version is available",
            },
            "system/routerboard": {
                "routerboard": "true",
                "current-firmware": "7.15.3",
                "upgrade-firmware": "7.16.2",
            },
        }.get(ep, {})
    )
    mock_client_rb.post = AsyncMock(return_value={})
    mock_client_rb.close = AsyncMock()

    with patch("src.api.v1.bulk_and_updates._create_client_from_vault", return_value=mock_client_rb):
        item_rb = await _probe_single_router_update(r_rb, "stable", t_id)
        assert item_rb.is_chr is False
        assert item_rb.action_plan == "ROUTERBOARD_OS_AND_FIRMWARE"
        assert item_rb.update_available is True
        assert item_rb.latest_version == "7.16.2"
        assert item_rb.current_firmware == "7.15.3"
        assert item_rb.upgrade_firmware == "7.16.2"


@pytest.mark.asyncio
async def test_execute_single_router_upgrade_chr_vs_routerboard() -> None:
    """Verifica que _execute_single_router_upgrade omite comandos RouterBOOT en CHR y los aplica en RouterBOARD."""
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    rid_chr = uuid.uuid4()
    rid_rb = uuid.uuid4()

    payload = RosUpdateExecuteRequest(
        router_ids=[rid_chr],
        channel="stable",
        auto_upgrade_firmware=True,
    )
    claims: dict[str, Any] = {"tid": str(t_id), "sub": str(u_id), "role": "TENANT_ADMIN"}

    r_chr = Router(id=rid_chr, display_name="chr-1", board_name="CHR Standard PC")
    r_rb = Router(id=rid_rb, display_name="rb-1", board_name="RB5009")

    client_chr = AsyncMock()
    client_chr.post = AsyncMock(return_value={"status": "installed"})
    client_rb = AsyncMock()
    client_rb.post = AsyncMock(return_value={"status": "installed"})

    db = AsyncMock()

    # Ejecución sobre CHR
    with patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(r_chr, client_chr)), \
         patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=True):
        res_chr, ok_chr = await _execute_single_router_upgrade(rid_chr, payload, claims, db, t_id, u_id, 0)
        assert ok_chr is True
        assert res_chr["mode"] == "CHR_OS_ONLY"
        assert res_chr["is_chr"] is True
        # Solo set channel, check-for-updates e install
        called_endpoints = [call.args[0] for call in client_chr.post.call_args_list]
        assert "system/package/update/set" in called_endpoints
        assert "system/package/update/install" in called_endpoints
        assert "system/routerboard/settings/set" not in called_endpoints
        assert "system/routerboard/upgrade" not in called_endpoints

    # Ejecución sobre RouterBOARD
    with patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(r_rb, client_rb)), \
         patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=True):
        res_rb, ok_rb = await _execute_single_router_upgrade(rid_rb, payload, claims, db, t_id, u_id, 0)
        assert ok_rb is True
        assert res_rb["mode"] == "ROUTERBOARD_OS_AND_FIRMWARE"
        assert res_rb["is_chr"] is False
        called_endpoints_rb = [call.args[0] for call in client_rb.post.call_args_list]
        assert "system/routerboard/settings/set" in called_endpoints_rb
        assert "system/routerboard/upgrade" in called_endpoints_rb
        assert "system/package/update/install" in called_endpoints_rb
