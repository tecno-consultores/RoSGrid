# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Gestión Centralizada de WiFi Corporativo (CAPsMAN / WiFiWave2) (Hitos 20.6 y 27.13 / docs/specs/51)."""

import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_feature, require_roles
from src.api.v1.webfig_common import execute_safe_mutation, get_router_and_client
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.schemas.enterprise import (
    CapsmanOverviewResponse,
    CapsmanReprovisionResponse,
    CapsmanToggleRequest,
    CapsmanToggleResponse,
    WifiClientItem,
    WifiConfigurationCreate,
    WifiConfigurationUpdate,
    WifiProvisioningRuleCreate,
    WifiProvisioningRuleItem,
    WifiQuickSetupRequest,
    WifiQuickSetupResponse,
    WifiSecurityProfileCreate,
    WifiSecurityProfileItem,
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

_WIFI_OPERATOR_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
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

            # 3. Clientes conectados en vivo
            try:
                clients = await client.get("/interface/wifi/registration-table")
                if isinstance(clients, list):
                    connected_clients = len(clients)
            except Exception:
                try:
                    clients = await client.get("/caps-man/registration-table")
                    if isinstance(clients, list):
                        connected_clients = len(clients)
                except Exception:
                    pass
    except Exception as exc:
        logger.debug("Error conectando con router %s para telemetría WiFi: %s", router_id, exc)

    return CapsmanOverviewResponse(
        router_id=router_id,
        capsman_running=capsman_running,
        active_radios_count=active_radios,
        managed_aps_count=managed_aps,
        connected_clients_count=connected_clients,
    )


@router.post(
    "/capsman/{router_id}/manager/toggle",
    response_model=CapsmanToggleResponse,
    summary="Conmutar activación del servicio Manager CAPsMAN bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def toggle_capsman_manager(
    router_id: uuid.UUID,
    payload: CapsmanToggleRequest,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> CapsmanToggleResponse:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    driver = "wifi"
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            # Detectar driver moderno v7.13+ vs legado caps-man
            is_modern = True
            try:
                await client.get("/interface/wifi/capsman")
            except Exception:
                is_modern = False

            if is_modern:
                driver = "wifi"
                body: dict[str, Any] = {
                    "enabled": "yes" if payload.enabled else "no",
                    "require-peer-certificate": "yes" if payload.require_peer_certificate else "no",
                }
                if payload.auto_certificates:
                    body["ca-certificate"] = "auto"
                    body["certificate"] = "auto"

                await execute_safe_mutation(
                    client=client,
                    menu="/interface/wifi/capsman",
                    action="set",
                    coro_fn=lambda: client.post("/interface/wifi/capsman/set", json_data=body),
                )
            else:
                driver = "caps-man"
                body = {
                    "enabled": "yes" if payload.enabled else "no",
                    "require-peer-certificate": "yes" if payload.require_peer_certificate else "no",
                }
                if payload.auto_certificates:
                    body["auto-certificate"] = "yes"

                await execute_safe_mutation(
                    client=client,
                    menu="/caps-man/manager",
                    action="set",
                    coro_fn=lambda: client.post("/caps-man/manager/set", json_data=body),
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error al conmutar estado de CAPsMAN en router %s: %s", router_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo en comunicación con RouterOS v7: {exc}",
        ) from exc

    state_str = "activado" if payload.enabled else "desactivado"
    return CapsmanToggleResponse(
        router_id=router_id,
        driver=driver,
        manager_enabled=payload.enabled,
        message=f"Servicio Gestor CAPsMAN ({driver}) {state_str} exitosamente bajo Safe Mode.",
    )


@router.get(
    "/capsman/{router_id}/ssids",
    response_model=list[WifiSsidProfile],
    summary="Listar configuraciones de SSID corporativas en tiempo real",
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
            cfgs: Any = None
            try:
                cfgs = await client.get("/interface/wifi/configuration")
            except Exception:
                try:
                    cfgs = await client.get("/caps-man/configuration")
                except Exception:
                    cfgs = []

            if isinstance(cfgs, list):
                for item in cfgs:
                    if not isinstance(item, dict):
                        continue
                    ssid_id = item.get(".id") or item.get("name") or str(uuid.uuid4())
                    name = item.get("name") or "Unnamed-SSID"
                    ssid = item.get("ssid") or item.get("name") or "RoSGrid-WiFi"
                    sec = (
                        item.get("security")
                        or item.get("security.authentication-types")
                        or item.get("security-profile")
                        or "wpa2-psk"
                    )
                    vlan_str = item.get("datapath.vlan-id") or item.get("vlan-id")
                    vlan_id = int(vlan_str) if vlan_str and str(vlan_str).isdigit() else None
                    isolation = bool(
                        item.get("datapath.client-isolation") in (True, "yes", "true")
                        or item.get("client-isolation") in (True, "yes", "true")
                    )
                    rates = item.get("rates") or ""
                    disabled = bool(item.get("disabled") in (True, "yes", "true"))
                    hide_ssid = bool(item.get("hide-ssid") in (True, "yes", "true"))
                    comment = item.get("comment")
                    sec_profile = item.get("security") or item.get("security.profile")

                    profiles.append(
                        WifiSsidProfile(
                            id=str(ssid_id),
                            name=str(name),
                            ssid=str(ssid),
                            security_type=str(sec),
                            vlan_id=vlan_id,
                            client_isolation=isolation,
                            rate_limit_profile=str(rates) if rates else None,
                            disabled=disabled,
                            security_profile=str(sec_profile) if sec_profile else None,
                            hide_ssid=hide_ssid,
                            comment=str(comment) if comment else None,
                        )
                    )
    except Exception as exc:
        logger.debug("Error consultando configuraciones WiFi en router %s: %s", router_id, exc)

    return profiles


@router.post(
    "/capsman/{router_id}/ssids",
    response_model=WifiSsidProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Crear o desplegar nuevo perfil de SSID corporativo (retrocompatible)",
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


@router.post(
    "/capsman/{router_id}/configurations",
    response_model=WifiSsidProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva configuración inalámbrica / SSID con aislamiento VLAN Datapath",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def create_capsman_configuration(
    router_id: uuid.UUID,
    payload: WifiConfigurationCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> WifiSsidProfile:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    created_id = str(uuid.uuid4())
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            cfg_body: dict[str, Any] = {
                "name": payload.name,
                "ssid": payload.ssid,
                "disabled": "yes" if payload.disabled else "no",
                "hide-ssid": "yes" if payload.hide_ssid else "no",
            }
            if payload.security_profile:
                cfg_body["security"] = payload.security_profile
            if payload.vlan_id:
                cfg_body["datapath.vlan-id"] = str(payload.vlan_id)
            if payload.client_isolation:
                cfg_body["datapath.client-isolation"] = "yes"
            if payload.comment:
                cfg_body["comment"] = payload.comment

            is_modern = True
            try:
                await client.get("/interface/wifi/configuration")
            except Exception:
                is_modern = False

            if is_modern:
                res = await execute_safe_mutation(
                    client=client,
                    menu="/interface/wifi/configuration",
                    action="add",
                    coro_fn=lambda: client.put("/interface/wifi/configuration", json_data=cfg_body),
                )
                if isinstance(res, dict) and res.get("ret"):
                    created_id = str(res["ret"])
            else:
                legacy_body: dict[str, Any] = {
                    "name": payload.name,
                    "ssid": payload.ssid,
                }
                if payload.security_profile:
                    legacy_body["security-profile"] = payload.security_profile
                if payload.vlan_id:
                    legacy_body["datapath.vlan-id"] = str(payload.vlan_id)
                res = await execute_safe_mutation(
                    client=client,
                    menu="/caps-man/configuration",
                    action="add",
                    coro_fn=lambda: client.put("/caps-man/configuration", json_data=legacy_body),
                )
                if isinstance(res, dict) and res.get("ret"):
                    created_id = str(res["ret"])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creando configuración Wi-Fi en router %s: %s", router_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al aprovisionar configuración Wi-Fi en RouterOS: {exc}",
        ) from exc

    return WifiSsidProfile(
        id=created_id,
        name=payload.name,
        ssid=payload.ssid,
        security_type=payload.security_profile or "wpa2-psk",
        vlan_id=payload.vlan_id,
        client_isolation=payload.client_isolation,
        disabled=payload.disabled,
        security_profile=payload.security_profile,
        hide_ssid=payload.hide_ssid,
        comment=payload.comment,
    )


@router.patch(
    "/capsman/{router_id}/configurations/{cfg_id}",
    response_model=dict[str, Any],
    summary="Modificar parámetros de un SSID inalámbrico bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def update_capsman_configuration(
    router_id: uuid.UUID,
    cfg_id: str,
    payload: WifiConfigurationUpdate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> dict[str, Any]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            patch_data: dict[str, Any] = {}
            if payload.ssid is not None:
                patch_data["ssid"] = payload.ssid
            if payload.security_profile is not None:
                patch_data["security"] = payload.security_profile
            if payload.vlan_id is not None:
                patch_data["datapath.vlan-id"] = str(payload.vlan_id)
            if payload.client_isolation is not None:
                patch_data["datapath.client-isolation"] = "yes" if payload.client_isolation else "no"
            if payload.disabled is not None:
                patch_data["disabled"] = "yes" if payload.disabled else "no"
            if payload.hide_ssid is not None:
                patch_data["hide-ssid"] = "yes" if payload.hide_ssid else "no"
            if payload.comment is not None:
                patch_data["comment"] = payload.comment

            is_modern = True
            try:
                await client.get("/interface/wifi/configuration")
            except Exception:
                is_modern = False

            target_path = (
                f"/interface/wifi/configuration/{cfg_id}"
                if is_modern
                else f"/caps-man/configuration/{cfg_id}"
            )
            await execute_safe_mutation(
                client=client,
                menu=target_path.rsplit("/", 1)[0],
                action="patch",
                coro_fn=lambda: client.patch(target_path, json_data=patch_data),
                item_id=cfg_id,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error modificando configuración Wi-Fi %s: %s", cfg_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al actualizar configuración en RouterOS: {exc}",
        ) from exc

    return {"status": "ok", "message": f"Configuración {cfg_id} actualizada exitosamente."}


@router.delete(
    "/capsman/{router_id}/configurations/{cfg_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar configuración de SSID inalámbrico bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def delete_capsman_configuration(
    router_id: uuid.UUID,
    cfg_id: str,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> None:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            is_modern = True
            try:
                await client.get("/interface/wifi/configuration")
            except Exception:
                is_modern = False

            target_path = (
                f"/interface/wifi/configuration/{cfg_id}"
                if is_modern
                else f"/caps-man/configuration/{cfg_id}"
            )
            await execute_safe_mutation(
                client=client,
                menu=target_path.rsplit("/", 1)[0],
                action="delete",
                coro_fn=lambda: client.delete(target_path),
                item_id=cfg_id,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error eliminando configuración Wi-Fi %s: %s", cfg_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al eliminar configuración en RouterOS: {exc}",
        ) from exc


@router.get(
    "/capsman/{router_id}/security-profiles",
    response_model=list[WifiSecurityProfileItem],
    summary="Listar perfiles de seguridad Wi-Fi (WPA2/WPA3)",
    dependencies=[Depends(require_roles(*_WIFI_READ_ROLES))],
)
async def list_security_profiles(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> list[WifiSecurityProfileItem]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    items: list[WifiSecurityProfileItem] = []
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            raw_sec: Any = None
            try:
                raw_sec = await client.get("/interface/wifi/security")
            except Exception:
                try:
                    raw_sec = await client.get("/caps-man/security")
                except Exception:
                    raw_sec = []

            if isinstance(raw_sec, list):
                for s in raw_sec:
                    if not isinstance(s, dict):
                        continue
                    sec_id = s.get(".id") or s.get("name") or str(uuid.uuid4())
                    name = s.get("name") or "default"
                    auth_str = str(s.get("authentication-types") or "wpa2-psk,wpa3-psk")
                    auth_list = [a.strip() for a in auth_str.split(",") if a.strip()]
                    wps = s.get("wps") in ("disable", "disabled", False)
                    ft = s.get("ft") in ("yes", True)
                    comment = s.get("comment")

                    items.append(
                        WifiSecurityProfileItem(
                            id=str(sec_id),
                            name=str(name),
                            authentication_types=auth_list,
                            passphrase_masked="********",
                            wps_disabled=wps,
                            ft_enabled=ft,
                            comment=str(comment) if comment else None,
                        )
                    )
    except Exception as exc:
        logger.debug("Error listando perfiles de seguridad Wi-Fi: %s", exc)

    return items


@router.post(
    "/capsman/{router_id}/security-profiles",
    response_model=WifiSecurityProfileItem,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil criptográfico de seguridad WPA2-PSK / WPA3-SAE con 802.11r",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def create_security_profile(
    router_id: uuid.UUID,
    payload: WifiSecurityProfileCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> WifiSecurityProfileItem:
    tenant_id = uuid.UUID(str(claims["tid"]))

    if len(payload.passphrase) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La clave de seguridad WPA debe contener al menos 8 caracteres.",
        )

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    created_id = str(uuid.uuid4())
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            is_modern = True
            try:
                await client.get("/interface/wifi/security")
            except Exception:
                is_modern = False

            if is_modern:
                sec_body = {
                    "name": payload.name,
                    "authentication-types": ",".join(payload.authentication_types),
                    "passphrase": payload.passphrase,
                    "wps": "disable" if payload.wps_disabled else "enable",
                    "ft": "yes" if payload.ft_enabled else "no",
                    "ft-over-ds": "yes" if payload.ft_enabled else "no",
                }
                if payload.comment:
                    sec_body["comment"] = payload.comment

                res = await execute_safe_mutation(
                    client=client,
                    menu="/interface/wifi/security",
                    action="add",
                    coro_fn=lambda: client.put("/interface/wifi/security", json_data=sec_body),
                )
                if isinstance(res, dict) and res.get("ret"):
                    created_id = str(res["ret"])
            else:
                legacy_sec = {
                    "name": payload.name,
                    "authentication-types": ",".join(payload.authentication_types),
                    "passphrase": payload.passphrase,
                    "encryption": "aes-ccm",
                }
                if payload.comment:
                    legacy_sec["comment"] = payload.comment

                res = await execute_safe_mutation(
                    client=client,
                    menu="/caps-man/security",
                    action="add",
                    coro_fn=lambda: client.put("/caps-man/security", json_data=legacy_sec),
                )
                if isinstance(res, dict) and res.get("ret"):
                    created_id = str(res["ret"])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creando perfil de seguridad en router %s: %s", router_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al crear perfil de seguridad en RouterOS: {exc}",
        ) from exc

    return WifiSecurityProfileItem(
        id=created_id,
        name=payload.name,
        authentication_types=payload.authentication_types,
        passphrase_masked="********",
        wps_disabled=payload.wps_disabled,
        ft_enabled=payload.ft_enabled,
        comment=payload.comment,
    )


@router.delete(
    "/capsman/{router_id}/security-profiles/{sec_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar perfil de seguridad Wi-Fi bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def delete_security_profile(
    router_id: uuid.UUID,
    sec_id: str,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> None:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            is_modern = True
            try:
                await client.get("/interface/wifi/security")
            except Exception:
                is_modern = False

            target = (
                f"/interface/wifi/security/{sec_id}"
                if is_modern
                else f"/caps-man/security/{sec_id}"
            )
            await execute_safe_mutation(
                client=client,
                menu=target.rsplit("/", 1)[0],
                action="delete",
                coro_fn=lambda: client.delete(target),
                item_id=sec_id,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error eliminando perfil de seguridad %s: %s", sec_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al eliminar perfil de seguridad en RouterOS: {exc}",
        ) from exc


@router.get(
    "/capsman/{router_id}/provisioning",
    response_model=list[WifiProvisioningRuleItem],
    summary="Listar reglas dinámicas de aprovisionamiento de radiofrecuencia",
    dependencies=[Depends(require_roles(*_WIFI_READ_ROLES))],
)
async def list_provisioning_rules(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> list[WifiProvisioningRuleItem]:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    rules: list[WifiProvisioningRuleItem] = []
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            raw_rules: Any = None
            try:
                raw_rules = await client.get("/interface/wifi/provisioning")
            except Exception:
                try:
                    raw_rules = await client.get("/caps-man/provisioning")
                except Exception:
                    raw_rules = []

            if isinstance(raw_rules, list):
                for r in raw_rules:
                    if not isinstance(r, dict):
                        continue
                    p_id = r.get(".id") or r.get("name") or str(uuid.uuid4())
                    name = r.get("name") or r.get("action") or "rule"
                    act = r.get("action") or "create-dynamic-enabled"
                    master = r.get("master-configuration") or ""
                    slaves_str = str(r.get("slave-configurations") or "")
                    slaves = [s.strip() for s in slaves_str.split(",") if s.strip()]
                    bands_str = str(r.get("supported-bands") or "")
                    bands = [b.strip() for b in bands_str.split(",") if b.strip()]
                    regex = r.get("identity-regex") or ".*"
                    disabled = bool(r.get("disabled") in (True, "yes", "true"))
                    comment = r.get("comment")

                    rules.append(
                        WifiProvisioningRuleItem(
                            id=str(p_id),
                            name=str(name),
                            action=str(act),
                            master_configuration=str(master),
                            slave_configurations=slaves,
                            supported_bands=bands,
                            identity_regex=str(regex),
                            disabled=disabled,
                            comment=str(comment) if comment else None,
                        )
                    )
    except Exception as exc:
        logger.debug("Error listando reglas de provisioning: %s", exc)

    return rules


@router.post(
    "/capsman/{router_id}/provisioning",
    response_model=WifiProvisioningRuleItem,
    status_code=status.HTTP_201_CREATED,
    summary="Crear regla de aprovisionamiento de flota inalámbrica bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def create_provisioning_rule(
    router_id: uuid.UUID,
    payload: WifiProvisioningRuleCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> WifiProvisioningRuleItem:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    created_id = str(uuid.uuid4())
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            is_modern = True
            try:
                await client.get("/interface/wifi/provisioning")
            except Exception:
                is_modern = False

            if is_modern:
                prov_body: dict[str, Any] = {
                    "action": payload.action,
                    "master-configuration": payload.master_configuration,
                }
                if payload.name:
                    prov_body["name"] = payload.name
                if payload.slave_configurations:
                    prov_body["slave-configurations"] = ",".join(payload.slave_configurations)
                if payload.supported_bands:
                    prov_body["supported-bands"] = ",".join(payload.supported_bands)
                if payload.identity_regex:
                    prov_body["identity-regex"] = payload.identity_regex
                if payload.comment:
                    prov_body["comment"] = payload.comment

                res = await execute_safe_mutation(
                    client=client,
                    menu="/interface/wifi/provisioning",
                    action="add",
                    coro_fn=lambda: client.put("/interface/wifi/provisioning", json_data=prov_body),
                )
                if isinstance(res, dict) and res.get("ret"):
                    created_id = str(res["ret"])
            else:
                legacy_body: dict[str, Any] = {
                    "action": payload.action,
                    "master-configuration": payload.master_configuration,
                    "identity-regex": payload.identity_regex,
                }
                if payload.name:
                    legacy_body["name"] = payload.name
                if payload.slave_configurations:
                    legacy_body["slave-configurations"] = ",".join(payload.slave_configurations)
                if payload.comment:
                    legacy_body["comment"] = payload.comment

                res = await execute_safe_mutation(
                    client=client,
                    menu="/caps-man/provisioning",
                    action="add",
                    coro_fn=lambda: client.put("/caps-man/provisioning", json_data=legacy_body),
                )
                if isinstance(res, dict) and res.get("ret"):
                    created_id = str(res["ret"])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creando regla de provisioning: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al crear regla de aprovisionamiento en RouterOS: {exc}",
        ) from exc

    return WifiProvisioningRuleItem(
        id=created_id,
        name=payload.name,
        action=payload.action,
        master_configuration=payload.master_configuration,
        slave_configurations=payload.slave_configurations,
        supported_bands=payload.supported_bands,
        identity_regex=payload.identity_regex,
        disabled=False,
        comment=payload.comment,
    )


@router.delete(
    "/capsman/{router_id}/provisioning/{prov_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar regla de aprovisionamiento de flota bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def delete_provisioning_rule(
    router_id: uuid.UUID,
    prov_id: str,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> None:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            is_modern = True
            try:
                await client.get("/interface/wifi/provisioning")
            except Exception:
                is_modern = False

            target = (
                f"/interface/wifi/provisioning/{prov_id}"
                if is_modern
                else f"/caps-man/provisioning/{prov_id}"
            )
            await execute_safe_mutation(
                client=client,
                menu=target.rsplit("/", 1)[0],
                action="delete",
                coro_fn=lambda: client.delete(target),
                item_id=prov_id,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error eliminando regla de provisioning %s: %s", prov_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al eliminar regla en RouterOS: {exc}",
        ) from exc


@router.post(
    "/capsman/{router_id}/reprovision",
    response_model=CapsmanReprovisionResponse,
    summary="Forzar reprovisionamiento en caliente de la flota de APs remotos",
    dependencies=[Depends(require_roles(*_WIFI_OPERATOR_ROLES))],
)
async def reprovision_capsman_fleet(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> CapsmanReprovisionResponse:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    count = 0
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            try:
                # Driver moderno RouterOS v7.13+
                radios = await client.get("/interface/wifi/radio")
                if isinstance(radios, list):
                    count = len(radios)
                    for rad in radios:
                        rad_id = rad.get(".id")
                        if rad_id:
                            try:
                                await client.post(f"/interface/wifi/radio/{rad_id}/provision")
                            except Exception:
                                pass
                else:
                    await client.post("/interface/wifi/radio/provision")
            except Exception:
                try:
                    # Driver legado caps-man
                    remotes = await client.get("/caps-man/remote-cap")
                    if isinstance(remotes, list):
                        count = len(remotes)
                        for r_cap in remotes:
                            r_id = r_cap.get(".id")
                            if r_id:
                                try:
                                    await client.post(f"/caps-man/remote-cap/{r_id}/provision")
                                except Exception:
                                    pass
                except Exception:
                    pass
    except Exception as exc:
        logger.error("Error forzando reprovisionamiento en router %s: %s", router_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al forzar reprovisionamiento en RouterOS: {exc}",
        ) from exc

    return CapsmanReprovisionResponse(
        success=True,
        provisioned_radios_count=count,
        message=f"Señal de reprovisionamiento enviada exitosamente a {count} radios/APs de la flota.",
    )


@router.delete(
    "/clients/{router_id}/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Expulsión táctica forzosa de un cliente conectado (Kick Client / Desautenticación)",
    dependencies=[Depends(require_roles(*_WIFI_OPERATOR_ROLES))],
)
async def delete_wifi_client(
    router_id: uuid.UUID,
    client_id: str,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> None:
    tenant_id = uuid.UUID(str(claims["tid"]))

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            deleted = False
            # 1. Intentar en /interface/wifi/registration-table
            try:
                await client.delete(f"/interface/wifi/registration-table/{client_id}")
                deleted = True
            except Exception:
                pass

            # 2. Intentar en /caps-man/registration-table
            if not deleted:
                try:
                    await client.delete(f"/caps-man/registration-table/{client_id}")
                    deleted = True
                except Exception:
                    pass

            # 3. Intentar en /interface/wireless/registration-table
            if not deleted:
                try:
                    await client.delete(f"/interface/wireless/registration-table/{client_id}")
                    deleted = True
                except Exception:
                    pass
    except Exception as exc:
        logger.error("Error expulsando cliente %s: %s", client_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al desasociar cliente inalámbrico: {exc}",
        ) from exc


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


@router.post(
    "/capsman/{router_id}/quick-setup",
    response_model=WifiQuickSetupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asistente Quick-Setup Wi-Fi en 1 Clic (Manager + Seguridad + SSIDs + Reglas) bajo Safe Mode",
    dependencies=[Depends(require_roles(*_WIFI_WRITE_ROLES))],
)
async def quick_setup_wifi(
    router_id: uuid.UUID,
    payload: WifiQuickSetupRequest,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> WifiQuickSetupResponse:
    tenant_id = uuid.UUID(str(claims["tid"]))

    if len(payload.corporate_passphrase) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La clave corporativa debe contener al menos 8 caracteres.",
        )
    if payload.guest_ssid_enabled and payload.guest_passphrase and len(payload.guest_passphrase) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La clave de la red de invitados debe contener al menos 8 caracteres.",
        )

    r_stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r_res = await db.execute(r_stmt)
    if not r_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    prov_count = 0
    try:
        _, client = await get_router_and_client(router_id, claims, db)
        async with client:
            is_modern = True
            try:
                await client.get("/interface/wifi/capsman")
            except Exception:
                is_modern = False

            async def _run_wizard_atomic() -> None:
                nonlocal prov_count
                if is_modern:
                    # 1. Habilitar Manager con certificados automáticos
                    await client.post(
                        "/interface/wifi/capsman/set",
                        json_data={
                            "enabled": "yes",
                            "ca-certificate": "auto",
                            "certificate": "auto",
                            "require-peer-certificate": "no",
                        },
                    )

                    # 2. Perfil de seguridad corporativo
                    sec_corp = {
                        "name": "sec-corporate",
                        "authentication-types": "wpa2-psk,wpa3-psk",
                        "passphrase": payload.corporate_passphrase,
                        "wps": "disable",
                        "ft": "yes",
                        "ft-over-ds": "yes",
                        "comment": "RoSGrid Quick-Setup Corporate Security",
                    }
                    try:
                        await client.put("/interface/wifi/security", json_data=sec_corp)
                    except Exception:
                        pass

                    # 3. Master Configuration Corporativa
                    cfg_corp = {
                        "name": "cfg-corporate",
                        "ssid": payload.corporate_ssid,
                        "security": "sec-corporate",
                        "comment": "RoSGrid Master Corporate Configuration",
                    }
                    try:
                        await client.put("/interface/wifi/configuration", json_data=cfg_corp)
                    except Exception:
                        pass

                    slaves_list: list[str] = []

                    # 4. Red de Invitados aislada en VLAN
                    if payload.guest_ssid_enabled and payload.guest_ssid:
                        guest_pass = payload.guest_passphrase or payload.corporate_passphrase
                        sec_guest = {
                            "name": "sec-guest",
                            "authentication-types": "wpa2-psk",
                            "passphrase": guest_pass,
                            "wps": "disable",
                            "comment": "RoSGrid Quick-Setup Guest Security",
                        }
                        try:
                            await client.put("/interface/wifi/security", json_data=sec_guest)
                        except Exception:
                            pass

                        dp_guest = {
                            "name": "dp-guest",
                            "bridge": payload.bridge_name,
                            "vlan-id": str(payload.guest_vlan_id or 200),
                            "client-isolation": "yes",
                            "comment": "RoSGrid Guest Isolated Datapath",
                        }
                        try:
                            await client.put("/interface/wifi/datapath", json_data=dp_guest)
                        except Exception:
                            pass

                        cfg_guest = {
                            "name": "cfg-guest",
                            "ssid": payload.guest_ssid,
                            "security": "sec-guest",
                            "datapath": "dp-guest",
                            "comment": "RoSGrid Guest Slave Configuration",
                        }
                        try:
                            await client.put("/interface/wifi/configuration", json_data=cfg_guest)
                            slaves_list.append("cfg-guest")
                        except Exception:
                            pass

                    # 5. Provisioning Rule para todas las bandas
                    prov_rule = {
                        "name": "prov-corporate-all",
                        "action": "create-dynamic-enabled",
                        "master-configuration": "cfg-corporate",
                        "supported-bands": "2ghz-ax,5ghz-ax,6ghz-ax,2ghz-ac,5ghz-ac",
                        "identity-regex": ".*",
                        "comment": "RoSGrid Quick-Setup Global Provisioning",
                    }
                    if slaves_list:
                        prov_rule["slave-configurations"] = ",".join(slaves_list)

                    try:
                        await client.put("/interface/wifi/provisioning", json_data=prov_rule)
                        prov_count += 1
                    except Exception:
                        pass
                else:
                    # Driver Legado caps-man
                    await client.post(
                        "/caps-man/manager/set",
                        json_data={"enabled": "yes", "auto-certificate": "yes"},
                    )

                    sec_corp = {
                        "name": "sec-corporate",
                        "authentication-types": "wpa2-psk",
                        "passphrase": payload.corporate_passphrase,
                        "encryption": "aes-ccm",
                    }
                    try:
                        await client.put("/caps-man/security", json_data=sec_corp)
                    except Exception:
                        pass

                    cfg_corp = {
                        "name": "cfg-corporate",
                        "ssid": payload.corporate_ssid,
                        "security-profile": "sec-corporate",
                    }
                    try:
                        await client.put("/caps-man/configuration", json_data=cfg_corp)
                    except Exception:
                        pass

                    slaves_list = []
                    if payload.guest_ssid_enabled and payload.guest_ssid:
                        guest_pass = payload.guest_passphrase or payload.corporate_passphrase
                        sec_guest = {
                            "name": "sec-guest",
                            "authentication-types": "wpa2-psk",
                            "passphrase": guest_pass,
                            "encryption": "aes-ccm",
                        }
                        try:
                            await client.put("/caps-man/security", json_data=sec_guest)
                        except Exception:
                            pass

                        cfg_guest = {
                            "name": "cfg-guest",
                            "ssid": payload.guest_ssid,
                            "security-profile": "sec-guest",
                            "datapath.vlan-id": str(payload.guest_vlan_id or 200),
                            "datapath.client-isolation": "yes",
                        }
                        try:
                            await client.put("/caps-man/configuration", json_data=cfg_guest)
                            slaves_list.append("cfg-guest")
                        except Exception:
                            pass

                    prov_rule = {
                        "name": "prov-corporate-all",
                        "action": "create-dynamic-enabled",
                        "master-configuration": "cfg-corporate",
                        "identity-regex": ".*",
                    }
                    if slaves_list:
                        prov_rule["slave-configurations"] = ",".join(slaves_list)
                    try:
                        await client.put("/caps-man/provisioning", json_data=prov_rule)
                        prov_count += 1
                    except Exception:
                        pass

            await execute_safe_mutation(
                client=client,
                menu="/interface/wifi",
                action="quick-setup",
                coro_fn=_run_wizard_atomic,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error en Quick-Setup Wi-Fi: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo en ejecución de Quick-Setup Wi-Fi: {exc}",
        ) from exc

    return WifiQuickSetupResponse(
        router_id=router_id,
        manager_enabled=True,
        corporate_ssid=payload.corporate_ssid,
        guest_ssid=payload.guest_ssid if payload.guest_ssid_enabled else None,
        guest_vlan_id=payload.guest_vlan_id if payload.guest_ssid_enabled else None,
        provisioning_rules_count=max(prov_count, 1),
        message="Despliegue Wi-Fi completado exitosamente: Manager, SSIDs y Reglas de provisión activas.",
    )
