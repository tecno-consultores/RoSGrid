# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Perfiles de Ancho de Banda (QoS) y Dispositivos de Abonados (Subscriber Devices).
Arquitectura de Cero Facturación y Cero Datos Personales (Identificación Técnica Exclusiva).
"""

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_feature, require_roles
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.models.ipam import (
    BandwidthProfile,
    CustomerServiceStatusEnum,
    SubscriberDevice,
)
from src.schemas.ipam import (
    BandwidthProfileCreate,
    BandwidthProfileResponse,
    BandwidthProfileUpdate,
    SubscriberDeviceCreate,
    SubscriberDeviceResponse,
    SubscriberDeviceUpdate,
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
    dependencies=[Depends(require_feature("isp_module_enabled"))],
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
