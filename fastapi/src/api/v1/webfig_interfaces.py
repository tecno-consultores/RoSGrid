# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebFig Capa 1: Interfaces, Óptica SFP DDM, Cable TDR, VLAN, Bridge, WireGuard y WiFi."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
)
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.schemas.webfig_l1_net import (
    BridgeCreateRequest,
    BridgePortCreateRequest,
    BridgeUpdateRequest,
    CablePairStatus,
    CableTestResponse,
    SfpDiagnosticsResponse,
    UpdateInterfaceRequest,
    VlanCreateRequest,
    VlanUpdateRequest,
    WireGuardCreateRequest,
    WireGuardPeerCreateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/interfaces", tags=["WebFig Interfaces"])


def _calculate_optical_health(rx_dbm: float | None) -> str:
    if rx_dbm is None:
        return "OPTIMAL"
    if rx_dbm >= -20.0:
        return "OPTIMAL"
    if rx_dbm >= -25.0:
        return "WARNING"
    return "CRITICAL_LOW_LIGHT"


def _parse_sfp_diagnostics(item_id: str, raw: dict[str, Any]) -> SfpDiagnosticsResponse:
    rx_val = raw.get("sfp-rx-power")
    rx_dbm = float(rx_val) if rx_val is not None else None
    tx_val = raw.get("sfp-tx-power")
    tx_dbm = float(tx_val) if tx_val is not None else None
    temp_val = raw.get("sfp-temperature")
    temp_c = float(temp_val) if temp_val is not None else None
    volt_val = raw.get("sfp-supply-voltage")
    volt_v = float(volt_val) if volt_val is not None else None
    bias_val = raw.get("sfp-tx-bias-current")
    bias_ma = float(bias_val) if bias_val is not None else None
    wave_val = raw.get("sfp-wavelength")
    wave_nm = int(wave_val) if wave_val is not None else None

    health = _calculate_optical_health(rx_dbm)
    return SfpDiagnosticsResponse(
        interface_id=item_id,
        interface_name=str(raw.get("name", item_id)),
        status=str(raw.get("status", "link-ok")),
        rate=str(raw.get("rate", "10Gbps")),
        full_duplex=raw.get("full-duplex", True) in (True, "true"),
        sfp_module_present=raw.get("sfp-module-present", True) in (True, "true"),
        sfp_vendor_name=raw.get("sfp-vendor-name"),
        sfp_part_number=raw.get("sfp-vendor-part-number"),
        sfp_wavelength_nm=wave_nm,
        sfp_temperature_c=temp_c,
        sfp_supply_voltage_v=volt_v,
        sfp_tx_bias_ma=bias_ma,
        sfp_tx_power_dbm=tx_dbm,
        sfp_rx_power_dbm=rx_dbm,
        optical_health=health,
    )


def _parse_cable_test(item_id: str, raw: dict[str, Any]) -> CableTestResponse:
    pairs = []
    for i in range(1, 5):
        st = raw.get(f"pair-{i}-status", "ok")
        len_val = raw.get(f"pair-{i}-cable-distance")
        dist = float(len_val) if len_val is not None else None
        pairs.append(CablePairStatus(pair=f"Pair {i}", status=str(st), length_meters=dist))
    return CableTestResponse(
        interface_id=item_id,
        interface_name=str(raw.get("name", item_id)),
        status=str(raw.get("status", "complete")),
        pairs=pairs,
    )


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("")
async def list_interfaces(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista todas las interfaces del router con estado de enlace y contadores."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface", client, refresh)


@router.patch("/{item_id}")
async def update_interface(
    router_id: uuid.UUID,
    item_id: str,
    payload: UpdateInterfaceRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica MTU, comentario o estado disabled de una interfaz bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data = payload.model_dump(exclude_unset=True)
    async with client:
        before = await client.get(f"/interface/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="interface",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/interface/{item_id}", json_data=patch_data),
        )


@router.get("/ethernet")
async def list_ethernet(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista interfaces físicas Ethernet, velocidades y puertos SFP."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/ethernet", client, refresh)


@router.post("/ethernet/{item_id}/sfp-monitor", response_model=SfpDiagnosticsResponse)
async def sfp_monitor(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> SfpDiagnosticsResponse:
    """Diagnóstico óptico DDM para puertos SFP/SFP+ (potencias TX/RX en dBm y salud óptica)."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        res = await client.post("/interface/ethernet/monitor", json_data={"numbers": item_id, "once": True})
        raw = res[0] if isinstance(res, list) and res else (res if isinstance(res, dict) else {})
        return _parse_sfp_diagnostics(item_id, raw)


@router.post("/ethernet/{item_id}/cable-test", response_model=CableTestResponse)
async def cable_test(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> CableTestResponse:
    """Ejecuta prueba TDR de integridad de pares de cable de cobre."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        res = await client.post("/interface/ethernet/cable-test", json_data={"numbers": item_id, "once": True})
        raw = res[0] if isinstance(res, list) and res else (res if isinstance(res, dict) else {})
        return _parse_cable_test(item_id, raw)


@router.get("/vlan")
async def list_vlans(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista interfaces VLAN 802.1Q."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/vlan", client, refresh)


@router.post("/vlan", status_code=status.HTTP_201_CREATED)
async def create_vlan(
    router_id: uuid.UUID,
    payload: VlanCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una nueva VLAN 802.1Q con protección Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body = {"name": payload.name, "vlan-id": payload.vlan_id, "interface": payload.interface}
    if payload.mtu:
        body["mtu"] = payload.mtu
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="interface/vlan",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/interface/vlan", json_data=body),
        )


@router.patch("/vlan/{item_id}")
async def update_vlan(
    router_id: uuid.UUID,
    item_id: str,
    payload: VlanUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica parámetros de una VLAN existente protegida por Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.name:
        patch_data["name"] = payload.name
    if payload.vlan_id:
        patch_data["vlan-id"] = payload.vlan_id
    if payload.interface:
        patch_data["interface"] = payload.interface
    if payload.mtu:
        patch_data["mtu"] = payload.mtu
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    if payload.comment is not None:
        patch_data["comment"] = payload.comment

    async with client:
        before = await client.get(f"/interface/vlan/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="interface/vlan",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/interface/vlan/{item_id}", json_data=patch_data),
        )


@router.delete("/vlan/{item_id}")
async def delete_vlan(
    router_id: uuid.UUID,
    item_id: str,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Elimina una VLAN bajo Safe Mode con deshabilitación preventiva."""
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        before = await client.get(f"/interface/vlan/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="interface/vlan",
            action="delete",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.delete(f"/interface/vlan/{item_id}"),
        )


@router.get("/bridge")
async def list_bridges(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista Bridges configurados."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/bridge", client, refresh)


@router.post("/bridge", status_code=status.HTTP_201_CREATED)
async def create_bridge(
    router_id: uuid.UUID,
    payload: BridgeCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea un nuevo Bridge bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {"name": payload.name, "vlan-filtering": payload.vlan_filtering}
    if payload.mtu:
        body["mtu"] = payload.mtu
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="interface/bridge",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/interface/bridge", json_data=body),
        )


@router.patch("/bridge/{item_id}")
async def update_bridge(
    router_id: uuid.UUID,
    item_id: str,
    payload: BridgeUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Modifica parámetros de un Bridge bajo Safe Mode (ej. activar vlan-filtering)."""
    _, client = await get_router_and_client(router_id, claims, db)
    patch_data: dict[str, Any] = {}
    if payload.name:
        patch_data["name"] = payload.name
    if payload.mtu:
        patch_data["mtu"] = payload.mtu
    if payload.vlan_filtering is not None:
        patch_data["vlan-filtering"] = payload.vlan_filtering
    if payload.disabled is not None:
        patch_data["disabled"] = payload.disabled
    if payload.comment is not None:
        patch_data["comment"] = payload.comment

    async with client:
        before = await client.get(f"/interface/bridge/{item_id}")
        return await execute_safe_mutation(
            client=client,
            menu="interface/bridge",
            action="set",
            item_id=item_id,
            before_state=before if isinstance(before, dict) else {},
            coro_fn=lambda: client.patch(f"/interface/bridge/{item_id}", json_data=patch_data),
        )


@router.get("/bridge/ports")
async def list_bridge_ports(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista puertos miembros de Bridges."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/bridge/port", client, refresh)


@router.post("/bridge/ports", status_code=status.HTTP_201_CREATED)
async def create_bridge_port(
    router_id: uuid.UUID,
    payload: BridgePortCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Agrega un puerto a un Bridge bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "bridge": payload.bridge,
        "interface": payload.interface,
        "pvid": payload.pvid,
        "hw": payload.hw,
    }
    if payload.frame_types:
        body["frame-types"] = payload.frame_types
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="interface/bridge/port",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/interface/bridge/port", json_data=body),
        )


@router.get("/bridge/vlans")
async def list_bridge_vlans(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista tabla de VLANs del Bridge."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/bridge/vlan", client, refresh)


@router.get("/bridge/hosts")
async def list_bridge_hosts(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista tabla FDB de direcciones MAC aprendidas en los Bridges."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/bridge/host", client, refresh)


@router.get("/wireguard")
async def list_wireguard(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista interfaces túnel WireGuard."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/wireguard", client, refresh)


@router.post("/wireguard", status_code=status.HTTP_201_CREATED)
async def create_wireguard(
    router_id: uuid.UUID,
    payload: WireGuardCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Crea una interfaz túnel WireGuard bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {"name": payload.name, "listen-port": payload.listen_port}
    if payload.mtu:
        body["mtu"] = payload.mtu
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="interface/wireguard",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/interface/wireguard", json_data=body),
        )


@router.get("/wireguard/peers")
async def list_wireguard_peers(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista Peers de WireGuard."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        return await cached_mikrotik_get(redis, tenant_id, router_id, "/interface/wireguard/peers", client, refresh)


@router.post("/wireguard/peers", status_code=status.HTTP_201_CREATED)
async def create_wireguard_peer(
    router_id: uuid.UUID,
    payload: WireGuardPeerCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.SUPERVISOR, SystemRoleEnum.SUPPORT_L3, SystemRoleEnum.SUPPORT_L2)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Registra un nuevo Peer WireGuard bajo Safe Mode."""
    _, client = await get_router_and_client(router_id, claims, db)
    body: dict[str, Any] = {
        "interface": payload.interface,
        "public-key": payload.public_key,
        "allowed-address": payload.allowed_address,
    }
    if payload.endpoint_address:
        body["endpoint-address"] = payload.endpoint_address
    if payload.endpoint_port:
        body["endpoint-port"] = payload.endpoint_port
    if payload.comment:
        body["comment"] = payload.comment
    async with client:
        return await execute_safe_mutation(
            client=client,
            menu="interface/wireguard/peers",
            action="create",
            before_state=body,
            coro_fn=lambda: client.put("/interface/wireguard/peers", json_data=body),
        )


@router.get("/wifi/registration-table")
async def list_wifi_registrations(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Lista clientes/estaciones inalámbricas asociadas (soporta drivers wifiwave2 y wireless legacy)."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = get_redis_client()
    _, client = await get_router_and_client(router_id, claims, db)
    async with client:
        try:
            return await cached_mikrotik_get(
                redis, tenant_id, router_id, "/interface/wifi/registration-table", client, refresh
            )
        except Exception:
            return await cached_mikrotik_get(
                redis, tenant_id, router_id, "/interface/wireless/registration-table", client, refresh
            )
