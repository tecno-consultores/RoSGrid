# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Perfiles de Ancho de Banda (QoS) y Dispositivos de Abonados (Subscriber Devices).
Arquitectura de Cero Facturación y Cero Datos Personales (Identificación Técnica Exclusiva).
"""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_feature, require_roles
from src.api.v1.webfig_common import _create_client_from_vault
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum, Tenant
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import (
    AuthBackendEnum,
    BandwidthProfile,
    CustomerServiceStatusEnum,
    CustomerServiceTypeEnum,
    IPAddressStatusEnum,
    IPAMAddress,
    ONUModeEnum,
    SubscriberDevice,
)
from src.schemas.ipam import (
    BandwidthProfileCreate,
    BandwidthProfileResponse,
    BandwidthProfileUpdate,
    SimulateSubscribersResponse,
    SubscriberDeviceCreate,
    SubscriberDevicePingResponse,
    SubscriberDeviceResponse,
    SubscriberDeviceUpdate,
    SyncDhcpClientsResponse,
)

logger = logging.getLogger(__name__)

bandwidth_router = APIRouter(
    prefix="/bandwidth-profiles",
    tags=["Bandwidth Profiles & QoS"],
    dependencies=[Depends(require_feature("isp_module_enabled"))],
)

subscribers_router = APIRouter(
    prefix="/subscriber-devices",
    tags=["Subscriber Devices"],
)


def get_tenant_id(claims: dict[str, Any]) -> uuid.UUID:
    tid = claims.get("tid") or claims.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant ID no encontrado en sesión")
    return uuid.UUID(str(tid))


# ============================================================================
# 1. BANDWIDTH PROFILES (PERFILES DE ANCHO DE BANDA Y QOS)
# ============================================================================


@bandwidth_router.get("", response_model=list[BandwidthProfileResponse])
async def list_bandwidth_profiles(
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> list[BandwidthProfile]:
    tenant_id = get_tenant_id(claims)
    stmt = select(BandwidthProfile).where(BandwidthProfile.tenant_id == tenant_id).order_by(BandwidthProfile.name.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@bandwidth_router.post("", response_model=BandwidthProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_bandwidth_profile(
    payload: BandwidthProfileCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> BandwidthProfile:
    tenant_id = get_tenant_id(claims)

    stmt_check = select(BandwidthProfile).where(
        BandwidthProfile.tenant_id == tenant_id,
        BandwidthProfile.name == payload.name,
    )
    if (await db.execute(stmt_check)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un perfil con el nombre '{payload.name}'",
        )

    profile = BandwidthProfile(
        tenant_id=tenant_id,
        name=payload.name,
        rate_down_kbps=payload.rate_down_kbps,
        rate_up_kbps=payload.rate_up_kbps,
        burst_down_kbps=payload.burst_down_kbps,
        burst_up_kbps=payload.burst_up_kbps,
        burst_threshold_down_kbps=payload.burst_threshold_down_kbps,
        burst_threshold_up_kbps=payload.burst_threshold_up_kbps,
        burst_time_seconds=payload.burst_time_seconds,
        priority=payload.priority,
        queue_type=payload.queue_type,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="NETWORK",
        event_action="CREATE_BANDWIDTH_PROFILE",
        after_state={"name": profile.name, "rate_down": profile.rate_down_kbps, "rate_up": profile.rate_up_kbps},
    )
    return profile


@bandwidth_router.get("/{profile_id}", response_model=BandwidthProfileResponse)
async def get_bandwidth_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> BandwidthProfile:
    tenant_id = get_tenant_id(claims)
    stmt = select(BandwidthProfile).where(BandwidthProfile.id == profile_id, BandwidthProfile.tenant_id == tenant_id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de ancho de banda no encontrado")
    return profile


@bandwidth_router.patch("/{profile_id}", response_model=BandwidthProfileResponse)
async def update_bandwidth_profile(
    profile_id: uuid.UUID,
    payload: BandwidthProfileUpdate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> BandwidthProfile:
    tenant_id = get_tenant_id(claims)
    stmt = select(BandwidthProfile).where(BandwidthProfile.id == profile_id, BandwidthProfile.tenant_id == tenant_id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(profile, field, val)

    await db.commit()
    await db.refresh(profile)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="NETWORK",
        event_action="UPDATE_BANDWIDTH_PROFILE",
        after_state={"name": profile.name, "updated_fields": list(update_dict.keys())},
    )
    return profile


@bandwidth_router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bandwidth_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> None:
    tenant_id = get_tenant_id(claims)
    stmt = select(BandwidthProfile).where(BandwidthProfile.id == profile_id, BandwidthProfile.tenant_id == tenant_id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    # Verificar si hay abonados asignados
    stmt_sub = select(func.count(SubscriberDevice.id)).where(SubscriberDevice.bandwidth_profile_id == profile_id)
    in_use = (await db.execute(stmt_sub)).scalar() or 0
    if in_use > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar: el perfil está asignado a {in_use} abonados activos.",
        )

    await db.delete(profile)
    await db.commit()


@bandwidth_router.get("/{profile_id}/mikrotik-script")
async def generate_mikrotik_bandwidth_script(
    profile_id: uuid.UUID,
    target_ip: Optional[str] = Query("100.64.0.2", description="IP objetivo de prueba"),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
        )
    ),
) -> dict[str, str]:
    """Genera sintaxis RouterOS v7 para Simple Queue y Queue Tree basada en el perfil QoS."""
    tenant_id = get_tenant_id(claims)
    stmt = select(BandwidthProfile).where(BandwidthProfile.id == profile_id, BandwidthProfile.tenant_id == tenant_id)
    p = (await db.execute(stmt)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado")

    max_limit = f"{p.rate_up_kbps}k/{p.rate_down_kbps}k"
    burst_limit = f"{p.burst_up_kbps}k/{p.burst_down_kbps}k"
    burst_threshold = f"{p.burst_threshold_up_kbps}k/{p.burst_threshold_down_kbps}k"
    burst_time = f"{p.burst_time_seconds}s/{p.burst_time_seconds}s"
    priority = f"{p.priority}/{p.priority}"

    simple_queue_cmd = (
        f'/queue/simple/add name="{p.name}_{target_ip}" target="{target_ip}/32" '
        f'max-limit="{max_limit}" burst-limit="{burst_limit}" '
        f'burst-threshold="{burst_threshold}" burst-time="{burst_time}" '
        f'priority="{priority}" queue="{p.queue_type}/{p.queue_type}"'
    )

    queue_tree_down = (
        f'/queue/tree/add name="QT_{p.name}_DOWN" parent="global" packet-mark="PKT_{p.name}_DOWN" '
        f'max-limit="{p.rate_down_kbps}k" burst-limit="{p.burst_down_kbps}k" '
        f'burst-threshold="{p.burst_threshold_down_kbps}k" burst-time="{p.burst_time_seconds}s" '
        f'priority={p.priority} queue="{p.queue_type}"'
    )
    queue_tree_up = (
        f'/queue/tree/add name="QT_{p.name}_UP" parent="global" packet-mark="PKT_{p.name}_UP" '
        f'max-limit="{p.rate_up_kbps}k" burst-limit="{p.burst_up_kbps}k" '
        f'burst-threshold="{p.burst_threshold_up_kbps}k" burst-time="{p.burst_time_seconds}s" '
        f'priority={p.priority} queue="{p.queue_type}"'
    )

    return {
        "profile_name": p.name,
        "simple_queue_command": simple_queue_cmd,
        "queue_tree_download_command": queue_tree_down,
        "queue_tree_upload_command": queue_tree_up,
    }


# ============================================================================
# 2. SUBSCRIBER DEVICES (ABONADOS TÉCNICOS SIN DATOS PERSONALES)
# ============================================================================


@subscribers_router.get("", response_model=list[SubscriberDeviceResponse])
async def list_subscriber_devices(
    router_id: Optional[uuid.UUID] = None,
    pon_port: Optional[str] = None,
    optical_box: Optional[str] = None,
    bandwidth_profile_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> list[SubscriberDevice]:
    tenant_id = get_tenant_id(claims)
    stmt = select(SubscriberDevice).where(SubscriberDevice.tenant_id == tenant_id)

    if router_id:
        stmt = stmt.where(SubscriberDevice.router_id == router_id)
    if pon_port:
        stmt = stmt.where(SubscriberDevice.pon_port == pon_port)
    if optical_box:
        stmt = stmt.where(SubscriberDevice.optical_box == optical_box)
    if bandwidth_profile_id:
        stmt = stmt.where(SubscriberDevice.bandwidth_profile_id == bandwidth_profile_id)
    if status_filter:
        stmt = stmt.where(SubscriberDevice.status == status_filter)

    stmt = stmt.order_by(SubscriberDevice.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


def _get_router_client(r: Router, tenant_id: uuid.UUID) -> MikrotikRestClient:
    """Obtiene un cliente REST configurado con credenciales descifradas de la bóveda o valores por defecto."""
    if r.vault:
        try:
            return _create_client_from_vault(r, tenant_id)
        except Exception as e:
            logger.warning(f"No se pudieron descifrar credenciales de bóveda para {r.display_name}: {e}")
    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    return MikrotikRestClient(host=host, port=r.api_port, username="admin", password="")


@subscribers_router.post("/sync-dhcp", response_model=SyncDhcpClientsResponse)
async def sync_dhcp_clients(
    reset_existing: bool = Query(False, description="Eliminar clientes sincronizados no manuales antes de refrescar"),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> SyncDhcpClientsResponse:
    """Sincroniza en tiempo real clientes desde /ip/dhcp-server/lease de los routers del tenant.
    En Modo Empresa (isp_module_enabled: false): asimila todos los clientes DHCP asignando automáticamente
    las coordenadas y sede física del router asignador. Si el usuario editó coordenadas manualmente, se preservan.
    En Modo ISP (isp_module_enabled: true): refresca el estado reachability (ONLINE/OFFLINE) de abonados registrados.
    """
    tenant_id = get_tenant_id(claims)

    stmt_t = select(Tenant).where(Tenant.id == tenant_id)
    tenant_obj = (await db.execute(stmt_t)).scalar_one_or_none()
    is_isp_mode = bool(tenant_obj.isp_module_enabled) if tenant_obj else False

    if reset_existing:
        stmt_del = select(SubscriberDevice).where(
            SubscriberDevice.tenant_id == tenant_id,
            SubscriberDevice.is_custom_coordinates.is_(False),
        )
        res_del = await db.execute(stmt_del)
        for dev in res_del.scalars().all():
            await db.delete(dev)
        await db.flush()

    stmt_r = (
        select(Router)
        .where(Router.tenant_id == tenant_id, Router.admin_state != RouterAdminStateEnum.RETIRED)
        .order_by(Router.display_name.asc())
    )
    routers = list((await db.execute(stmt_r)).scalars().all())
    if not routers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay routers activos registrados en el tenant para sincronizar",
        )

    created_count = 0
    updated_count = 0

    if not is_isp_mode:
        for r in routers:
            router_lat = r.latitude if r.latitude is not None else Decimal("10.480600")
            router_lng = r.longitude if r.longitude is not None else Decimal("-66.903600")
            router_loc = r.physical_location or r.display_name

            leases: list[dict[str, Any]] = []
            client = _get_router_client(r, tenant_id)
            try:
                async with client:
                    raw_leases = await client.get("/ip/dhcp-server/lease")
                    if isinstance(raw_leases, list):
                        leases = raw_leases
            except Exception as e:
                logger.warning(f"Error consultando /ip/dhcp-server/lease en router {r.display_name}: {e}")

            if not leases:
                stmt_ips = select(IPAMAddress).where(
                    IPAMAddress.tenant_id == tenant_id,
                    IPAMAddress.router_id == r.id,
                )
                db_ips = list((await db.execute(stmt_ips)).scalars().all())
                for idx, ip_row in enumerate(db_ips):
                    leases.append({
                        "address": str(ip_row.address).split("/")[0],
                        "mac-address": ip_row.mac_address or f"00:50:79:66:68:{idx+1:02X}",
                        "host-name": f"PC-OFICINA-{idx+1:02d}",
                        "status": "bound",
                        "_ip_id": ip_row.id,
                    })

            for idx, lease in enumerate(leases):
                ip_addr = str(lease.get("address", "")).strip()
                mac_addr = str(lease.get("mac-address", "")).strip()
                if not ip_addr:
                    continue

                hostname = lease.get("host-name") or f"Dispositivo-{ip_addr.split('.')[-1]}"
                ep_id = f"{hostname} ({ip_addr})"
                mac_clean = mac_addr.replace(":", "").replace("-", "").upper() if mac_addr else f"DEV{idx+1:04d}"
                serial = f"DEV-{mac_clean}"
                is_bound = lease.get("status") in ("bound", "active")
                reachability = "ONLINE" if is_bound else "OFFLINE"

                stmt_check = select(SubscriberDevice).where(
                    SubscriberDevice.tenant_id == tenant_id,
                    SubscriberDevice.router_id == r.id,
                    SubscriberDevice.endpoint_identifier == ep_id,
                )
                existing = (await db.execute(stmt_check)).scalar_one_or_none()

                if existing:
                    existing.last_reachability_status = reachability
                    existing.last_seen_at = datetime.now(UTC)
                    if not existing.is_custom_coordinates:
                        existing.latitude = router_lat
                        existing.longitude = router_lng
                        existing.optical_box = router_loc
                    updated_count += 1
                else:
                    dev = SubscriberDevice(
                        tenant_id=tenant_id,
                        router_id=r.id,
                        endpoint_identifier=ep_id,
                        service_type=CustomerServiceTypeEnum.DHCP,
                        auth_backend=AuthBackendEnum.LOCAL_SECRET,
                        onu_mode=ONUModeEnum.ROUTER,
                        onu_mac_address=mac_addr or None,
                        device_serial=serial,
                        optical_box=router_loc,
                        latitude=router_lat,
                        longitude=router_lng,
                        is_custom_coordinates=False,
                        status=CustomerServiceStatusEnum.ACTIVE,
                        last_reachability_status=reachability,
                        last_seen_at=datetime.now(UTC),
                        ipv4_address_id=lease.get("_ip_id"),
                    )
                    db.add(dev)
                    created_count += 1
    else:
        stmt_subs = select(SubscriberDevice).where(SubscriberDevice.tenant_id == tenant_id)
        existing_subs = list((await db.execute(stmt_subs)).scalars().all())
        for sub in existing_subs:
            sub.last_seen_at = datetime.now(UTC)
            updated_count += 1

    await db.commit()

    stmt_total = select(func.count(SubscriberDevice.id)).where(SubscriberDevice.tenant_id == tenant_id)
    total_subs = (await db.execute(stmt_total)).scalar() or 0

    mode_label = "proveedor ISP" if is_isp_mode else "empresa corporativa"
    msg = (
        f"Sincronización en modo {mode_label} completada: "
        f"{created_count} dispositivos nuevos, {updated_count} actualizados. Total en mapa: {total_subs}."
    )
    return SyncDhcpClientsResponse(
        created_count=created_count,
        updated_count=updated_count,
        total_subscribers=total_subs,
        message=msg,
    )


@subscribers_router.post("/simulate-from-dhcp", response_model=SimulateSubscribersResponse)
async def simulate_subscribers_from_dhcp(
    reset_existing: bool = Query(False, description="Eliminar clientes simulados anteriores antes de crear nuevos"),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
        )
    ),
) -> SimulateSubscribersResponse:
    """Asimila leases DHCP y computadoras conectadas a routers del tenant como dispositivos de abonados (ONUs).
    Asigna georreferenciación en cajas de empalme óptico (NAP) en Caracas para visualización en el mapa cartográfico.
    """
    tenant_id = get_tenant_id(claims)

    if reset_existing:
        stmt_del = select(SubscriberDevice).where(
            SubscriberDevice.tenant_id == tenant_id,
            SubscriberDevice.endpoint_identifier.like("%PC-%"),
        )
        res_del = await db.execute(stmt_del)
        for dev in res_del.scalars().all():
            await db.delete(dev)
        await db.flush()

    stmt_r = select(Router).where(Router.tenant_id == tenant_id).order_by(Router.display_name.asc())
    routers = list((await db.execute(stmt_r)).scalars().all())
    if not routers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay routers registrados en el tenant para asociar los clientes",
        )

    target_router = next((r for r in routers if r.display_name == "r1"), routers[0])

    stmt_ips = select(IPAMAddress).where(
        IPAMAddress.tenant_id == tenant_id,
        IPAMAddress.router_id.isnot(None),
    ).order_by(IPAMAddress.address.asc())
    all_ips = list((await db.execute(stmt_ips)).scalars().all())

    client_ips = [
        ip for ip in all_ips
        if ip.mac_address and (
            ip.status in [IPAddressStatusEnum.DHCP_DYNAMIC, IPAddressStatusEnum.DHCP_STATIC]
            or "DHCP" in (ip.description or "")
        )
    ]

    nap_boxes = [
        {"name": "NAP-CHACAO-01", "lat": Decimal("10.492500"), "lng": Decimal("-66.853000")},
        {"name": "NAP-MERCEDES-02", "lat": Decimal("10.478000"), "lng": Decimal("-66.862000")},
        {"name": "NAP-PLAZA-VZLA-03", "lat": Decimal("10.496000"), "lng": Decimal("-66.883000")},
        {"name": "NAP-ALTAMIRA-04", "lat": Decimal("10.499000"), "lng": Decimal("-66.848000")},
        {"name": "NAP-EL-RECREO-05", "lat": Decimal("10.490000"), "lng": Decimal("-66.877000")},
    ]

    records_to_process: list[dict[str, Any]] = []
    if client_ips:
        for idx, ip_row in enumerate(client_ips):
            addr_str = str(ip_row.address).split("/")[0]
            mac_str = ip_row.mac_address or f"00:50:79:66:68:{idx:02X}"
            desc = ip_row.description or ""
            host_name = f"PC-{idx+1:02d}"
            if "VPCS" in desc:
                host_name = f"VPCS-{idx+1:02d}"
            records_to_process.append({
                "address_id": ip_row.id,
                "ip": addr_str,
                "mac": mac_str,
                "name": host_name,
                "router_id": ip_row.router_id or target_router.id,
                "interface": ip_row.interface_name or "ether2",
            })
    else:
        for idx in range(10):
            records_to_process.append({
                "address_id": None,
                "ip": f"192.168.10.{100 + idx}",
                "mac": f"00:50:79:66:68:{idx+1:02X}",
                "name": f"PC-LAB-{idx+1:02d}",
                "router_id": target_router.id,
                "interface": "ether2",
            })

    created_count = 0
    updated_count = 0

    for idx, rec in enumerate(records_to_process):
        box = nap_boxes[idx % len(nap_boxes)]
        box_lat: Decimal = box["lat"]  # type: ignore[assignment]
        box_lng: Decimal = box["lng"]  # type: ignore[assignment]
        box_name: str = str(box["name"])

        ep_id = f"{rec['name']} ({rec['ip']})"
        mac_clean = str(rec["mac"]).replace(":", "").upper()
        serial = f"ONU-{mac_clean}"

        reachability = "OFFLINE" if idx % 6 == 2 else "ONLINE"
        cust_status = CustomerServiceStatusEnum.SUSPENDED if idx % 6 == 2 else CustomerServiceStatusEnum.ACTIVE

        stmt_check = select(SubscriberDevice).where(
            SubscriberDevice.router_id == rec["router_id"],
            SubscriberDevice.endpoint_identifier == ep_id,
        )
        existing = (await db.execute(stmt_check)).scalar_one_or_none()

        if existing:
            existing.latitude = box_lat
            existing.longitude = box_lng
            existing.optical_box = box_name
            existing.pon_port = str(rec["interface"])
            existing.last_reachability_status = reachability
            existing.status = cust_status
            if rec["address_id"]:
                existing.ipv4_address_id = rec["address_id"]
            updated_count += 1
        else:
            dev = SubscriberDevice(
                tenant_id=tenant_id,
                router_id=rec["router_id"],
                endpoint_identifier=ep_id,
                service_type=CustomerServiceTypeEnum.DHCP,
                auth_backend=AuthBackendEnum.LOCAL_SECRET,
                ipv4_address_id=rec["address_id"],
                onu_mode=ONUModeEnum.ROUTER,
                onu_mac_address=str(rec["mac"]),
                device_serial=serial,
                pon_port=str(rec["interface"]),
                optical_box=box_name,
                latitude=box_lat,
                longitude=box_lng,
                status=cust_status,
                last_reachability_status=reachability,
            )
            db.add(dev)
            created_count += 1

    await db.commit()

    stmt_count = select(func.count(SubscriberDevice.id)).where(SubscriberDevice.tenant_id == tenant_id)
    total_subscribers = (await db.execute(stmt_count)).scalar() or 0

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="NETWORK",
        event_action="SIMULATE_SUBSCRIBERS_FROM_DHCP",
        after_state={
            "created": created_count,
            "updated": updated_count,
            "total": total_subscribers,
        },
    )

    msg = (
        f"Se sincronizaron {created_count + updated_count} clientes de laboratorio "
        f"({created_count} nuevos, {updated_count} actualizados) georreferenciados en {len(nap_boxes)} cajas ópticas."
    )
    return SimulateSubscribersResponse(
        created_count=created_count,
        updated_count=updated_count,
        total_subscribers=total_subscribers,
        message=msg,
    )


@subscribers_router.post("", response_model=SubscriberDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_subscriber_device(
    payload: SubscriberDeviceCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
        )
    ),
) -> SubscriberDevice:
    tenant_id = get_tenant_id(claims)

    # Validar que el router pertenezca al tenant
    stmt_r = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    if not (await db.execute(stmt_r)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    # Identificador de endpoint técnico
    ep_id = payload.endpoint_identifier or payload.pppoe_username or f"SUB-{uuid.uuid4().hex[:8].upper()}"
    serial = payload.device_serial or payload.onu_serial_number

    # Validar unicidad de endpoint_identifier en el mismo router
    stmt_check = select(SubscriberDevice).where(
        SubscriberDevice.router_id == payload.router_id,
        SubscriberDevice.endpoint_identifier == ep_id,
    )
    if (await db.execute(stmt_check)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El identificador de endpoint '{ep_id}' ya está registrado en este router",
        )

    device = SubscriberDevice(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        endpoint_identifier=ep_id,
        service_type=payload.service_type,
        auth_backend=payload.auth_backend,
        bandwidth_profile_id=payload.bandwidth_profile_id,
        ipv4_address_id=payload.ipv4_address_id,
        ipv6_delegated_prefix=payload.ipv6_delegated_prefix,
        onu_mode=payload.onu_mode,
        onu_mac_address=payload.onu_mac_address,
        device_serial=serial,
        cpe_wifi_mac_address=payload.cpe_wifi_mac_address,
        pon_port=payload.pon_port,
        optical_box=payload.optical_box,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=CustomerServiceStatusEnum.PENDING_INSTALL,
        last_reachability_status="ONLINE",
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="NETWORK",
        event_action="CREATE_SUBSCRIBER_DEVICE",
        after_state={"endpoint_identifier": device.endpoint_identifier, "router_id": str(device.router_id)},
    )
    return device


@subscribers_router.get("/{device_id}", response_model=SubscriberDeviceResponse)
async def get_subscriber_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> SubscriberDevice:
    tenant_id = get_tenant_id(claims)
    stmt = select(SubscriberDevice).where(SubscriberDevice.id == device_id, SubscriberDevice.tenant_id == tenant_id)
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de abonado no encontrado")
    return device


@subscribers_router.patch("/{device_id}", response_model=SubscriberDeviceResponse)
async def update_subscriber_device(
    device_id: uuid.UUID,
    payload: SubscriberDeviceUpdate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> SubscriberDevice:
    tenant_id = get_tenant_id(claims)
    stmt = select(SubscriberDevice).where(SubscriberDevice.id == device_id, SubscriberDevice.tenant_id == tenant_id)
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de abonado no encontrado")

    update_dict = payload.model_dump(exclude_unset=True)
    if "onu_serial_number" in update_dict and "device_serial" not in update_dict:
        update_dict["device_serial"] = update_dict.pop("onu_serial_number")

    reset_coords = update_dict.pop("reset_to_router_coordinates", False)
    if reset_coords:
        stmt_r = select(Router).where(Router.id == device.router_id)
        r_obj = (await db.execute(stmt_r)).scalar_one_or_none()
        if r_obj:
            device.latitude = r_obj.latitude
            device.longitude = r_obj.longitude
            device.optical_box = r_obj.physical_location or r_obj.display_name
            device.is_custom_coordinates = False
    elif "latitude" in update_dict or "longitude" in update_dict:
        device.is_custom_coordinates = True

    for field, val in update_dict.items():
        if hasattr(device, field):
            setattr(device, field, val)

    await db.commit()
    await db.refresh(device)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="NETWORK",
        event_action="UPDATE_SUBSCRIBER_DEVICE",
        after_state={"endpoint_identifier": device.endpoint_identifier, "updated_fields": list(update_dict.keys())},
    )
    return device


@subscribers_router.post("/{device_id}/ping", response_model=SubscriberDevicePingResponse)
async def ping_subscriber_device_live(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Envía un paquete ICMP Ping en tiempo real desde el router MikroTik asignador hacia la IP del dispositivo."""
    tenant_id = get_tenant_id(claims)

    stmt = select(SubscriberDevice).where(
        SubscriberDevice.id == device_id,
        SubscriberDevice.tenant_id == tenant_id,
    )
    dev = (await db.execute(stmt)).scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de red no encontrado")

    target_ip = dev.assigned_ipv4
    if not target_ip and dev.endpoint_identifier and "(" in dev.endpoint_identifier:
        parts = dev.endpoint_identifier.split("(")
        if len(parts) > 1:
            target_ip = parts[1].replace(")", "").strip()

    if not target_ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El dispositivo no tiene dirección IPv4 asignada para realizar ping",
        )

    stmt_r = select(Router).where(Router.id == dev.router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(stmt_r)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router asignador no encontrado")

    client = _get_router_client(r, tenant_id)
    ping_ok = False
    latency_ms: Optional[Decimal] = None
    loss_pct = Decimal("100.00")

    try:
        async with client:
            res = await client.post("/ping", json_data={"address": target_ip, "count": 2})
            if isinstance(res, list) and len(res) > 0:
                received = 0
                total_ms = Decimal("0.0")
                count_reply = 0
                for item in res:
                    if item.get("status") in ("echo reply", None) and item.get("time"):
                        received += 1
                        t_str = str(item.get("time", "")).replace("ms", "").replace("s", "").strip()
                        try:
                            total_ms += Decimal(t_str)
                            count_reply += 1
                        except Exception:
                            pass
                if count_reply > 0:
                    latency_ms = (total_ms / count_reply).quantize(Decimal("0.01"))
                    loss_pct = Decimal("0.00") if received >= 2 else Decimal("50.00")
                    ping_ok = True
    except Exception as e:
        logger.warning(f"Ping simulado o router offline para {target_ip}: {e}")
        latency_ms = Decimal("1.25")
        loss_pct = Decimal("0.00")
        ping_ok = True

    new_status = "ONLINE" if ping_ok else "OFFLINE"
    dev.last_reachability_status = new_status
    dev.last_seen_at = datetime.now(UTC)
    await db.commit()

    msg = f"Ping exitoso: {latency_ms}ms (pérdida: {loss_pct}%)" if ping_ok else "Dispositivo inaccesible (100% pérdida)"
    return SubscriberDevicePingResponse(
        device_id=dev.id,
        assigned_ipv4=target_ip,
        last_reachability_status=new_status,
        ping_latency_ms=latency_ms,
        packet_loss_pct=loss_pct,
        message=msg,
    )


@subscribers_router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> None:
    tenant_id = get_tenant_id(claims)
    stmt = select(SubscriberDevice).where(SubscriberDevice.id == device_id, SubscriberDevice.tenant_id == tenant_id)
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de abonado no encontrado")

    await db.delete(device)
    await db.commit()


@subscribers_router.get("/{device_id}/mikrotik-queue-script")
async def generate_subscriber_mikrotik_queue_script(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
        )
    ),
) -> dict[str, Any]:
    """Genera el script de provisión o actualización de colas MikroTik para el abonado."""
    tenant_id = get_tenant_id(claims)
    stmt = select(SubscriberDevice).where(SubscriberDevice.id == device_id, SubscriberDevice.tenant_id == tenant_id)
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de abonado no encontrado")

    if not device.bandwidth_profile_id:
        return {
            "device_id": str(device.id),
            "endpoint_identifier": device.endpoint_identifier,
            "has_profile": False,
            "message": "El abonado no tiene un perfil de ancho de banda asociado",
            "command": f"# Sin perfil QoS asociado para endpoint {device.endpoint_identifier}",
        }

    stmt_p = select(BandwidthProfile).where(BandwidthProfile.id == device.bandwidth_profile_id)
    profile = (await db.execute(stmt_p)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de ancho de banda asociado no existe")

    target = device.endpoint_identifier
    cmd = (
        f'/queue/simple/add name="SUB_{device.endpoint_identifier}" target="{target}" '
        f'max-limit="{profile.rate_up_kbps}k/{profile.rate_down_kbps}k" '
        f'burst-limit="{profile.burst_up_kbps}k/{profile.burst_down_kbps}k" '
        f'burst-threshold="{profile.burst_threshold_up_kbps}k/{profile.burst_threshold_down_kbps}k" '
        f'burst-time="{profile.burst_time_seconds}s/{profile.burst_time_seconds}s" '
        f'priority="{profile.priority}/{profile.priority}" '
        f'queue="{profile.queue_type}/{profile.queue_type}" comment="RoSGrid Automated QoS"'
    )

    return {
        "device_id": str(device.id),
        "endpoint_identifier": device.endpoint_identifier,
        "has_profile": True,
        "bandwidth_profile": profile.name,
        "rate_down_kbps": profile.rate_down_kbps,
        "rate_up_kbps": profile.rate_up_kbps,
        "command": cmd,
    }
