# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Pruebas unitarias Level-11X para Actualización Inteligente RouterOS v7 + Firmware y Auto-Detección CHR (Hito 28.1)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.api.v1.bulk_and_updates import (
    _DEFAULT_STARTER_TEMPLATES,
    _cleanup_corrupted_npk_downloads,
    _execute_single_router_upgrade,
    _fetch_latest_version_via_http_fallback,
    _install_routeros_via_fetch_fallback,
    _is_chr_router,
    _probe_routerboard_safe,
    _probe_single_router_update,
    _resolve_npk_package_filename,
    _run_router_template_steps,
    _should_skip_step_for_router,
)
from src.api.v1.webfig_system_tools import _fetch_system_routerboard
from src.mikrotik.client import MikrotikApiError
from src.models.inventory import Router, RouterCredentialsVault
from src.schemas.bulk_and_updates import (
    RosUpdateExecuteRequest,
)


def test_starter_template_15_exists_and_schema() -> None:
    """Verifica que la plantilla #15 existe en _DEFAULT_STARTER_TEMPLATES con sus esquemas y parámetros."""
    tpl = next((t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "ACTUALIZACION_ROUTEROS_Y_FIRMWARE"), None)
    assert tpl is not None, "Plantilla ACTUALIZACION_ROUTEROS_Y_FIRMWARE debe estar presente en el catálogo"
    assert tpl["category"] == "SYSTEM"
    assert tpl["requires_safemode"] is False, (
        "Las actualizaciones con reinicio de OS deben tener requires_safemode=False"
    )

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
    # Se llamaron 3 endpoints de plantilla + 1 file/print de limpieza preventiva .npk
    post_endpoints = [call.args[0] for call in client.post.call_args_list if call.args]
    assert "file/print" in post_endpoints
    assert len([ep for ep in post_endpoints if ep != "file/print"]) == 3


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
    # Se llamaron 5 endpoints de plantilla + 1 file/print de limpieza preventiva .npk
    post_endpoints = [call.args[0] for call in client.post.call_args_list if call.args]
    assert "file/print" in post_endpoints
    assert len([ep for ep in post_endpoints if ep != "file/print"]) == 5


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
    with (
        patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(r_chr, client_chr)),
        patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=True),
    ):
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
    with (
        patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(r_rb, client_rb)),
        patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=True),
    ):
        res_rb, ok_rb = await _execute_single_router_upgrade(rid_rb, payload, claims, db, t_id, u_id, 0)
        assert ok_rb is True
        assert res_rb["mode"] == "ROUTERBOARD_OS_AND_FIRMWARE"
        assert res_rb["is_chr"] is False
        called_endpoints_rb = [call.args[0] for call in client_rb.post.call_args_list]
        assert "system/routerboard/settings/set" in called_endpoints_rb
        assert "system/routerboard/upgrade" in called_endpoints_rb
        assert "system/package/update/install" in called_endpoints_rb


@pytest.mark.asyncio
async def test_chr_routerboard_400_tolerance_and_corrupted_npk_cleanup() -> None:
    """Verifica tolerancia a HTTP 400 en system/routerboard en CHR y limpieza de .npk corruptos de 0 bytes."""
    r_chr = Router(display_name="caps1", board_name="CHR VMware")
    r_unknown = Router(display_name="vm-x86", board_name="x86_64")

    client = AsyncMock()
    client.get = AsyncMock(
        side_effect=lambda ep: (
            (_ for _ in ()).throw(MikrotikApiError(400, "no such command or directory (routerboard)"))
            if ep == "system/routerboard"
            else [
                {".id": "*10", "name": "downloads/routeros-7.25.1.npk", "size": "0"},
                {".id": "*11", "name": "routeros-7.25.1.npk", "size": "20892689"},
            ]
        )
    )
    client.delete = AsyncMock(return_value=None)

    # Si is_chr=True, ni siquiera invoca system/routerboard
    rb_chr = await _probe_routerboard_safe(client, r_chr, is_chr=True, cur_fw=None, upg_fw=None)
    assert rb_chr == (True, None, None)

    # Si is_chr=False pero el equipo lanza 400 (ej. CHR sin board_name previo), devuelve (True, None, None)
    rb_unknown_chr = await _probe_routerboard_safe(client, r_unknown, is_chr=False, cur_fw="7.21", upg_fw="7.25")
    assert rb_unknown_chr == (True, None, None)

    # También en webfig_system_tools._fetch_system_routerboard
    rb_sys = await _fetch_system_routerboard(client)
    assert rb_sys == {}

    # Limpieza de .npk corruptos (0 bytes)
    removed_count = await _cleanup_corrupted_npk_downloads(client)
    assert removed_count == 1
    client.delete.assert_called_once_with("file/*10")


def test_resolve_npk_package_filename_architectures() -> None:
    """Verifica el nombre de paquete .npk según arquitectura (x86_64/CHR vs arm64 vs mmips)."""
    assert _resolve_npk_package_filename("7.25.1", "x86_64") == "routeros-7.25.1.npk"
    assert _resolve_npk_package_filename("7.25.1", None) == "routeros-7.25.1.npk"
    assert _resolve_npk_package_filename("7.25.1", "arm64") == "routeros-7.25.1-arm64.npk"
    assert _resolve_npk_package_filename("7.25.1", "mmips (MIPS)") == "routeros-7.25.1-mmips.npk"


@pytest.mark.asyncio
async def test_routeros_725_bad_http_response_fallback_check_and_install() -> None:
    """Verifica el fallback mediante /tool/fetch cuando RouterOS 7.25 devuelve 'ERROR: bad HTTP response'."""
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    rid_chr = uuid.uuid4()

    r_chr = Router(
        id=rid_chr,
        tenant_id=t_id,
        display_name="caps1",
        board_name="CHR VMware",
        architecture_name="x86_64",
        ros_version="7.25 (stable)",
    )

    client = AsyncMock()

    async def mock_get(ep: str, timeout: float | None = None) -> Any:
        if ep == "system/package/update":
            return {
                "channel": "stable",
                "installed-version": "7.25",
                "status": "ERROR: bad HTTP response",
            }
        if ep == "file":
            return [{".id": "*5", "name": "routeros-7.25.1.npk", "size": "20892689"}]
        return {}

    async def mock_post(
        ep: str,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        if ep in ("system/package/update/check-for-updates", "system/package/update/install"):
            return [
                {
                    "channel": "stable",
                    "installed-version": "7.25",
                    "status": "ERROR: bad HTTP response",
                }
            ]
        if ep == "tool/fetch":
            url = (json_data or {}).get("url", "")
            if "NEWESTa7" in url:
                return [{"status": "finished", "data": "7.25.1 1793623193\n"}]
            return [{"status": "finished", "downloaded": "20403"}]
        return {"status": "ok"}

    client.get = AsyncMock(side_effect=mock_get)
    client.post = AsyncMock(side_effect=mock_post)
    client.delete = AsyncMock(return_value=None)

    # 1. Prueba directa de _fetch_latest_version_via_http_fallback
    ver = await _fetch_latest_version_via_http_fallback(client, "stable")
    assert ver == "7.25.1"

    # 2. Prueba directa de _install_routeros_via_fetch_fallback
    inst_res = await _install_routeros_via_fetch_fallback(client, r_chr, "stable", "7.25.1")
    assert inst_res["status"] == "INSTALLED_VIA_FETCH_FALLBACK"
    assert inst_res["target_version"] == "7.25.1"

    # Restaurar versión pre-upgrade para prueba integrada
    r_chr.ros_version = "7.25 (stable)"

    # 3. Prueba integrada en _execute_single_router_upgrade con RouterOS 7.25 afectado por bug de fetch
    payload = RosUpdateExecuteRequest(
        router_ids=[rid_chr],
        channel="stable",
        auto_upgrade_firmware=True,
    )
    claims: dict[str, Any] = {"tid": str(t_id), "sub": str(u_id), "role": "SUPERADMIN_GLOBAL"}
    db = AsyncMock()

    with (
        patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(r_chr, client)),
        patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=True),
    ):
        res_upg, ok_upg = await _execute_single_router_upgrade(rid_chr, payload, claims, db, t_id, u_id, 0)
        assert ok_upg is True
        assert res_upg["status"] == "UPGRADE_TRIGGERED"
        assert res_upg["installed_version"] == "7.25"
        assert res_upg["target_version"] == "7.25.1"


@pytest.mark.asyncio
async def test_starter_template_17_system_clock_timezone_schema_and_execution() -> None:
    """Verifica la plantilla #17 HUSO_HORARIO_SISTEMA (/system/clock/set) y su ejecución REST."""
    from src.api.v1.bulk_and_updates import _execute_single_step, _render_template_steps

    tpl = next((t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "HUSO_HORARIO_SISTEMA"), None)
    assert tpl is not None, "Plantilla HUSO_HORARIO_SISTEMA debe existir en _DEFAULT_STARTER_TEMPLATES"
    assert tpl["category"] == "SYSTEM"
    assert tpl["requires_safemode"] is True

    vars_by_key = {v["key"]: v for v in tpl["variables_schema"]}
    assert "time_zone_name" in vars_by_key
    assert vars_by_key["time_zone_name"]["default_val"] == "America/Caracas"
    assert vars_by_key["time_zone_name"]["var_type"] == "select"
    assert "America/Caracas" in vars_by_key["time_zone_name"]["options"]
    assert "UTC" in vars_by_key["time_zone_name"]["options"]

    assert "time_zone_autodetect" in vars_by_key
    assert vars_by_key["time_zone_autodetect"]["default_val"] == "no"
    assert vars_by_key["time_zone_autodetect"]["var_type"] == "select"
    assert vars_by_key["time_zone_autodetect"]["options"] == ["no", "yes"]

    rendered = _render_template_steps(
        tpl["rest_steps_template"],
        {"time_zone_name": "America/Caracas", "time_zone_autodetect": "no"},
    )
    assert len(rendered) == 1
    assert rendered[0]["method"] == "POST"
    assert rendered[0]["endpoint"] == "system/clock/set"
    assert rendered[0]["payload"] == {
        "time-zone-autodetect": "no",
        "time-zone-name": "America/Caracas",
    }

    client = AsyncMock()
    client.post = AsyncMock(return_value={"status": "ok"})
    router_chr = Router(
        id=uuid.uuid4(),
        display_name="caps1",
        board_name="CHR VMware",
    )

    summary = await _run_router_template_steps(
        client=client,
        router_obj=router_chr,
        rendered_steps=rendered,
        vars_dict={"time_zone_name": "America/Caracas", "time_zone_autodetect": "no"},
    )
    assert "POST /rest/system/clock/set -> OK" in summary
    client.post.assert_awaited_once_with(
        "system/clock/set",
        {"time-zone-autodetect": "no", "time-zone-name": "America/Caracas"},
    )

    # Verificar que PATCH sobre el menú singleton 'system/clock' también se convierte a POST 'system/clock/set'
    client.post.reset_mock()
    await _execute_single_step(
        client,
        "PATCH",
        "system/clock",
        {"time-zone-name": "UTC"},
    )
    client.post.assert_awaited_once_with("system/clock/set", {"time-zone-name": "UTC"})


@pytest.mark.asyncio
async def test_perform_pre_upgrade_backup_uses_export_router_rsc_and_rejects_empty_brackets() -> None:
    """Verifica que _perform_pre_upgrade_backup usa export_router_rsc, deduplica y nunca guarda '[]'."""
    from unittest.mock import MagicMock

    from src.api.v1.bulk_and_updates import _perform_pre_upgrade_backup

    client = AsyncMock()
    r_chr = Router(id=uuid.uuid4(), display_name="caps1", ros_version="7.25.1")
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    db = AsyncMock()
    mock_exec = MagicMock()
    mock_exec.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_exec

    with patch(
        "src.api.v1.backups.export_router_rsc",
        AsyncMock(return_value="/system identity\nset name=caps"),
    ):
        ok = await _perform_pre_upgrade_backup(client, r_chr, t_id, u_id, db)
        assert ok is True
        db.add.assert_called_once()
        saved_bk = db.add.call_args[0][0]
        assert saved_bk.rsc_size_bytes > 2
        assert not saved_bk.rsc_sha256_hash.startswith("4f53cda18c2baa")
