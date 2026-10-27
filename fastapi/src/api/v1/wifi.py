# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Gestión Centralizada de WiFi Corporativo (CAPsMAN / WiFiWave2) (Hito 20.6 / docs/specs/33 §6)."""

import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_feature, require_roles
from src.api.v1.webfig_common import get_router_and_client
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.schemas.enterprise import (
    CapsmanOverviewResponse,
    WifiClientItem,
    WifiSsidProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/wifi",
    tags=["Enterprise WiFi & CAPsMAN"],
    dependencies=[Depends(require_feature("capsman_wifi_enabled"))],
)

_WIFI_READ_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.NOC_MONITOR,
)

_WIFI_WRITE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
)


@router.get(
    "/capsman/{router_id}/overview",
    response_model=CapsmanOverviewResponse,
    summary="Consultar estado operativo del controlador WiFi CAPsMAN / WiFiWave2",
    dependencies=[Depends(require_roles(*_WIFI_READ_ROLES))],
)
async def get_capsman_overview(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> CapsmanOverviewResponse:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    router_obj = r_res.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    active_radios = 0
    managed_aps = 0
    connected_clients = 0
    capsman_running = False

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            # 1. Consultar estado del manager CAPsMAN (RouterOS v7 wifi o legacy caps-man)
            try:
                wifi_caps = await client.get("/interface/wifi/capsman")
                if isinstance(wifi_caps, dict) and str(wifi_caps.get("enabled", "")).lower() in ("true", "yes"):
                    capsman_running = True
            except Exception:
                try:
                    mgr = await client.get("/caps-man/manager")
                    if isinstance(mgr, dict) and str(mgr.get("enabled", "")).lower() in ("true", "yes"):
                        capsman_running = True
                except Exception:
                    pass

            # 2. Consultar radios / APs remotos
            try:
                radios = await client.get("/interface/wifi/capsman/remote-cap")
                if isinstance(radios, list):
                    managed_aps = len(radios)
                    active_radios = sum(int(r.get("radios", 1)) for r in radios if isinstance(r, dict)) if managed_aps > 0 else 0
            except Exception:
                try:
                    radios = await client.get("/caps-man/remote-cap")
                    if isinstance(radios, list):
                        managed_aps = len(radios)
                        active_radios = sum(int(r.get("radios", 1)) for r in radios if isinstance(r, dict)) if managed_aps > 0 else 0
                except Exception:
                    pass

            # Si no hay remote-caps pero hay radios locales WiFiWave2
            if active_radios == 0:
                try:
                    local_radios = await client.get("/interface/wifi/radio")
                    if isinstance(local_radios, list):
                        active_radios = len(local_radios)
                except Exception:
                    pass

            # 3. Consultar registration-table
            try:
                reg_table = await client.get("/interface/wifi/registration-table")
                if isinstance(reg_table, list):
                    connected_clients = len(reg_table)
            except Exception:
                try:
                    reg_table = await client.get("/caps-man/registration-table")
                    if isinstance(reg_table, list):
                        connected_clients = len(reg_table)
                except Exception:
                    pass

            if managed_aps > 0 or connected_clients > 0:
                capsman_running = True
    except Exception as exc:
        logger.debug("Sondeo CAPsMAN REST en router %s: %s", router_id, exc)

    return CapsmanOverviewResponse(
        router_id=router_obj.id,
        capsman_running=capsman_running,
        active_radios_count=active_radios,
        managed_aps_count=managed_aps,
        connected_clients_count=connected_clients,
    )


@router.get(
    "/capsman/{router_id}/ssids",
    response_model=list[WifiSsidProfile],
    summary="Listar perfiles de SSIDs inalámbricos orquestados por CAPsMAN",
    dependencies=[Depends(require_roles(*_WIFI_READ_ROLES))],
)
async def list_capsman_ssids(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> list[WifiSsidProfile]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    profiles: list[WifiSsidProfile] = []
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            configs: Any = None
            try:
                configs = await client.get("/interface/wifi/configuration")
            except Exception:
                try:
                    configs = await client.get("/caps-man/configuration")
                except Exception:
                    configs = []

            if isinstance(configs, list):
                for idx, item in enumerate(configs):
                    if not isinstance(item, dict):
                        continue
                    ssid_id = item.get(".id") or item.get("name") or f"ssid-{idx}"
                    name = item.get("name", f"Profile-{idx}")
                    ssid = item.get("ssid", name)
                    sec = (
                        item.get("security.authentication-types")
                        or item.get("security", "WPA2/WPA3")
                    )
                    vlan = item.get("datapath.vlan-id") or item.get("vlan-id")
                    try:
                        vlan_id = int(vlan) if vlan is not None else None
                    except (ValueError, TypeError):
                        vlan_id = None
                    isolation = bool(
                        item.get("datapath.client-isolation") in (True, "yes", "true")
                    )
                    rates = item.get("rates") or ""
                    profiles.append(
                        WifiSsidProfile(
                            id=str(ssid_id),
                            name=str(name),
                            ssid=str(ssid),
                            security_type=str(sec),
                            vlan_id=vlan_id,
                            client_isolation=isolation,
                            rate_limit_profile=str(rates) if rates else None,
                        )
                    )
    except Exception as exc:
        logger.debug("Error consultando configuraciones WiFi en router %s: %s", router_id, exc)

    return profiles


@router.post(
    "/capsman/{router_id}/ssids",
    response_model=WifiSsidProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Crear o desplegar nuevo perfil de SSID corporativo",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def create_capsman_ssid(
    router_id: uuid.UUID,
    payload: WifiSsidProfile,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> WifiSsidProfile:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            cfg_body: dict[str, Any] = {
                "name": payload.name,
                "ssid": payload.ssid,
            }
            if payload.vlan_id:
                cfg_body["datapath.vlan-id"] = str(payload.vlan_id)
            if payload.client_isolation:
                cfg_body["datapath.client-isolation"] = "yes"
            try:
                await client.put("/interface/wifi/configuration", json_data=cfg_body)
            except Exception:
                try:
                    await client.put("/caps-man/configuration", json_data=cfg_body)
                except Exception as exc:
                    logger.debug("No se pudo aprovisionar perfil en hardware RouterOS: %s", exc)
    except Exception as exc:
        logger.debug("Error conectando con router %s para crear SSID: %s", router_id, exc)

    return payload


@router.get(
    "/clients/{router_id}",
    response_model=list[WifiClientItem],
    summary="Listar clientes WiFi en tiempo real con RSSI, SNR y trazabilidad Fast Roaming (802.11r/k/v)",
    dependencies=[Depends(require_roles(*_WIFI_READ_ROLES))],
)
async def list_wifi_clients(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> list[WifiClientItem]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    clients_list: list[WifiClientItem] = []
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            reg_table: Any = None
            try:
                reg_table = await client.get("/interface/wifi/registration-table")
            except Exception:
                try:
                    reg_table = await client.get("/caps-man/registration-table")
                except Exception:
                    try:
                        reg_table = await client.get("/interface/wireless/registration-table")
                    except Exception:
                        reg_table = []

            if isinstance(reg_table, list):
                for r in reg_table:
                    if not isinstance(r, dict):
                        continue
                    mac = r.get("mac-address") or r.get(".id", "")
                    if not mac:
                        continue
                    signal_val = r.get("signal") or r.get("rx-signal") or -70
                    try:
                        signal_rssi = int(signal_val)
                    except (ValueError, TypeError):
                        signal_rssi = -70

                    snr_val = r.get("snr") or 25
                    try:
                        snr_db = int(snr_val)
                    except (ValueError, TypeError):
                        snr_db = 25

                    std = r.get("standard") or r.get("band") or "Wi-Fi"
                    tx = r.get("tx-rate", "0")
                    rx = r.get("rx-rate", "0")
                    try:
                        tx_mbps = float(str(tx).lower().replace("mbps", "").strip() or 0)
                    except (ValueError, TypeError):
                        tx_mbps = 0.0
                    try:
                        rx_mbps = float(str(rx).lower().replace("mbps", "").strip() or 0)
                    except (ValueError, TypeError):
                        rx_mbps = 0.0

                    fast_roam = bool(r.get("802.11r") or r.get("fast-roaming") or False)

                    uptime_str = str(r.get("uptime", "0s"))
                    uptime_secs = 0
                    try:
                        hours = re.search(r"(\d+)h", uptime_str)
                        mins = re.search(r"(\d+)m", uptime_str)
                        secs = re.search(r"(\d+)s", uptime_str)
                        if hours:
                            uptime_secs += int(hours.group(1)) * 3600
                        if mins:
                            uptime_secs += int(mins.group(1)) * 60
                        if secs:
                            uptime_secs += int(secs.group(1))
                    except Exception:
                        uptime_secs = 0

                    clients_list.append(
                        WifiClientItem(
                            mac_address=str(mac),
                            ip_address=r.get("ip-address"),
                            hostname=r.get("hostname"),
                            ap_name=r.get("interface") or r.get("ap", "CAP-AP"),
                            ssid=r.get("ssid", ""),
                            signal_rssi_dbm=signal_rssi,
                            snr_db=snr_db,
                            wifi_standard=str(std),
                            tx_rate_mbps=tx_mbps,
                            rx_rate_mbps=rx_mbps,
                            fast_roaming_supported=fast_roam,
                            connected_duration_seconds=uptime_secs or 0,
                        )
                    )
    except Exception as exc:
        logger.debug("Error consultando clientes WiFi en router %s: %s", router_id, exc)

    return clients_list
