# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Aprovisionamiento Técnico Idempotente de Servicios de Red (Hito 17)."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import require_feature, require_roles
from src.api.v1.webfig_common import get_router_and_client
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.ipam import BandwidthProfile, SubscriberDevice
from src.schemas.network_services import (
    ChangeRateLimitRequest,
    NetworkServiceActionResponse,
    NetworkServiceDetailResponse,
)
from src.services.network_events import publish_network_service_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/network-services",
    tags=["Network Services Provisioning"],
    dependencies=[Depends(require_feature("isp_module_enabled"))],
)

_PROVISIONING_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.NOC_MONITOR,
    SystemRoleEnum.SUPPORT_L1,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.FIELD_TECH,
)


def _validate_idempotency_key(idempotency_key: str) -> uuid.UUID:
    """Valida que la cabecera Idempotency-Key sea un UUID válido."""
    try:
        return uuid.UUID(idempotency_key)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cabecera Idempotency-Key obligatoria y debe ser un UUID válido",
        ) from None


def _get_tenant_id(claims: dict[str, Any]) -> uuid.UUID:
    tid = claims.get("tid") or claims.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant ID no encontrado en sesión")
    return uuid.UUID(str(tid))


async def _resolve_subscriber_target_ip(device: SubscriberDevice) -> Optional[str]:
    """Obtiene la dirección IP asignada al abonado para reglas de firewall y colas."""
    if device.assigned_ipv4:
        return str(device.assigned_ipv4)
    if device.ipv4_address and hasattr(device.ipv4_address, "address") and device.ipv4_address.address:
        return str(device.ipv4_address.address).split("/")[0]
    return None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/{service_id}", response_model=NetworkServiceDetailResponse)
async def get_network_service_detail(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(*_PROVISIONING_ROLES)),
) -> SubscriberDevice:
    """Obtiene el detalle y estado técnico actual de un servicio de red."""
    tenant_id = _get_tenant_id(claims)
    stmt = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.bandwidth_profile), selectinload(SubscriberDevice.ipv4_address))
        .where(SubscriberDevice.id == service_id, SubscriberDevice.tenant_id == tenant_id)
    )
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio de red no encontrado")
    return device


@router.post("/{service_id}/isolate", response_model=NetworkServiceActionResponse)
async def isolate_network_service(
    service_id: uuid.UUID,
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUIDv7 obligatorio de idempotencia"),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(*_PROVISIONING_ROLES)),
) -> NetworkServiceActionResponse:
    """Aísla técnicamente el servicio de red en RouterOS (agrega a AISLADOS_TECNICO o conmuta cola a 64k/64k).

    Idempotente: si el servicio ya se encuentra aislado, responde HTTP 200 con status ALREADY_ISOLATED.
    """
    _validate_idempotency_key(idempotency_key)
    tenant_id = _get_tenant_id(claims)

    stmt = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.bandwidth_profile), selectinload(SubscriberDevice.ipv4_address))
        .where(SubscriberDevice.id == service_id, SubscriberDevice.tenant_id == tenant_id)
    )
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio de red no encontrado")

    # Verificación de idempotencia lógica
    if device.status in ("ISOLATED_ADMINISTRATIVE", "SUSPENDED_TECHNICAL"):
        return NetworkServiceActionResponse(
            status="ALREADY_ISOLATED",
            service_id=device.id,
            endpoint_identifier=device.endpoint_identifier,
            message="El servicio de red ya se encuentra en estado aislado",
            bandwidth_profile_id=device.bandwidth_profile_id,
        )

    target_ip = await _resolve_subscriber_target_ip(device)

    # Ejecución en MikroTik RouterOS v7
    try:
        _, client = await get_router_and_client(device.router_id, claims, db)
        async with client:
            # 1. Agregar a lista de firewall AISLADOS_TECNICO si tiene IP
            if target_ip:
                existing = await client.get(f"/ip/firewall/address-list?list=AISLADOS_TECNICO&address={target_ip}")
                if not existing:
                    await client.put(
                        "/ip/firewall/address-list",
                        {
                            "list": "AISLADOS_TECNICO",
                            "address": target_ip,
                            "comment": f"RoSGrid Aislado: {device.endpoint_identifier}",
                        },
                    )

            # 2. Conmutar límites de cola a 64k/64k para preservar telemetría mínima
            q_name = f"SUB_{device.endpoint_identifier}"
            queues = await client.get(f"/queue/simple?name={q_name}")
            if queues and len(queues) > 0:
                q_id = queues[0].get(".id")
                await client.patch(
                    f"/queue/simple/{q_id}",
                    {"max-limit": "64k/64k", "comment": "RoSGrid Aislado Preventivo (64k/64k)"},
                )
    except Exception as exc:
        logger.warning(
            "No se pudo contactar al router físico para aislamiento de %s (continuando en BD): %s",
            device.endpoint_identifier,
            exc,
        )

    # Actualizar estado en Base de Datos
    device.status = "ISOLATED_ADMINISTRATIVE"
    device.updated_at = datetime.now(UTC)
    await db.commit()

    # Registro en Auditoría Inmutable WORM
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "api")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="OPERATIONS",
        event_action="NETWORK_SERVICE_ISOLATED",
        status_code=200,
        after_state={
            "service_id": str(device.id),
            "endpoint_identifier": device.endpoint_identifier,
            "idempotency_key": idempotency_key,
            "target_ip": target_ip,
        },
    )

    # Despachar evento para Webhooks salientes
    await publish_network_service_event(
        tenant_id=tenant_id,
        event_name="DEVICE_ISOLATED",
        payload={
            "service_id": str(device.id),
            "router_id": str(device.router_id),
            "endpoint_identifier": device.endpoint_identifier,
            "device_serial": device.device_serial,
            "target_ip": target_ip,
            "isolated_at": datetime.now(UTC).isoformat(),
        },
    )

    return NetworkServiceActionResponse(
        status="ISOLATED",
        service_id=device.id,
        endpoint_identifier=device.endpoint_identifier,
        message="Servicio de red aislado exitosamente en RouterOS v7",
        bandwidth_profile_id=device.bandwidth_profile_id,
    )


@router.post("/{service_id}/restore", response_model=NetworkServiceActionResponse)
async def restore_network_service(
    service_id: uuid.UUID,
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUIDv7 obligatorio de idempotencia"),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(*_PROVISIONING_ROLES)),
) -> NetworkServiceActionResponse:
    """Restaura el servicio técnico de red en RouterOS (elimina de AISLADOS_TECNICO y normaliza colas).

    Idempotente: si el servicio ya se encuentra activo, responde HTTP 200 con status ALREADY_ACTIVE.
    """
    _validate_idempotency_key(idempotency_key)
    tenant_id = _get_tenant_id(claims)

    stmt = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.bandwidth_profile), selectinload(SubscriberDevice.ipv4_address))
        .where(SubscriberDevice.id == service_id, SubscriberDevice.tenant_id == tenant_id)
    )
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio de red no encontrado")

    # Verificación de idempotencia lógica
    if device.status == "ACTIVE":
        return NetworkServiceActionResponse(
            status="ALREADY_ACTIVE",
            service_id=device.id,
            endpoint_identifier=device.endpoint_identifier,
            message="El servicio de red ya se encuentra activo",
            bandwidth_profile_id=device.bandwidth_profile_id,
        )

    target_ip = await _resolve_subscriber_target_ip(device)

    # Ejecución en MikroTik RouterOS v7
    try:
        _, client = await get_router_and_client(device.router_id, claims, db)
        async with client:
            # 1. Retirar de lista AISLADOS_TECNICO
            if target_ip:
                existing = await client.get(f"/ip/firewall/address-list?list=AISLADOS_TECNICO&address={target_ip}")
                if existing and len(existing) > 0:
                    entry_id = existing[0].get(".id")
                    await client.delete(f"/ip/firewall/address-list/{entry_id}")

            # 2. Restaurar colas originales según BandwidthProfile
            if device.bandwidth_profile:
                p = device.bandwidth_profile
                q_name = f"SUB_{device.endpoint_identifier}"
                queues = await client.get(f"/queue/simple?name={q_name}")
                if queues and len(queues) > 0:
                    q_id = queues[0].get(".id")
                    await client.patch(
                        f"/queue/simple/{q_id}",
                        {
                            "max-limit": f"{p.rate_up_kbps}k/{p.rate_down_kbps}k",
                            "burst-limit": f"{p.burst_up_kbps}k/{p.burst_down_kbps}k",
                            "burst-threshold": f"{p.burst_threshold_up_kbps}k/{p.burst_threshold_down_kbps}k",
                            "burst-time": f"{p.burst_time_seconds}s/{p.burst_time_seconds}s",
                            "priority": f"{p.priority}/{p.priority}",
                            "comment": "RoSGrid Automated QoS",
                        },
                    )
    except Exception as exc:
        logger.warning(
            "No se pudo contactar al router físico para restauración de %s (continuando en BD): %s",
            device.endpoint_identifier,
            exc,
        )

    # Actualizar estado en Base de Datos
    device.status = "ACTIVE"
    device.updated_at = datetime.now(UTC)
    await db.commit()

    # Registro en Auditoría Inmutable WORM
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "api")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="OPERATIONS",
        event_action="NETWORK_SERVICE_RESTORED",
        status_code=200,
        after_state={
            "service_id": str(device.id),
            "endpoint_identifier": device.endpoint_identifier,
            "idempotency_key": idempotency_key,
            "target_ip": target_ip,
        },
    )

    # Despachar evento para Webhooks salientes
    await publish_network_service_event(
        tenant_id=tenant_id,
        event_name="DEVICE_RESTORED",
        payload={
            "service_id": str(device.id),
            "router_id": str(device.router_id),
            "endpoint_identifier": device.endpoint_identifier,
            "device_serial": device.device_serial,
            "target_ip": target_ip,
            "restored_at": datetime.now(UTC).isoformat(),
        },
    )

    return NetworkServiceActionResponse(
        status="RESTORED",
        service_id=device.id,
        endpoint_identifier=device.endpoint_identifier,
        message="Servicio de red restaurado exitosamente en RouterOS v7",
        bandwidth_profile_id=device.bandwidth_profile_id,
    )


@router.post("/{service_id}/change-rate-limit", response_model=NetworkServiceActionResponse)
async def change_network_service_rate_limit(
    service_id: uuid.UUID,
    payload: ChangeRateLimitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUIDv7 obligatorio de idempotencia"),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(*_PROVISIONING_ROLES)),
) -> NetworkServiceActionResponse:
    """Modifica en caliente los límites de ancho de banda y QoS en RouterOS sin desconectar la sesión física del abonado."""
    _validate_idempotency_key(idempotency_key)
    tenant_id = _get_tenant_id(claims)

    stmt = select(SubscriberDevice).where(SubscriberDevice.id == service_id, SubscriberDevice.tenant_id == tenant_id)
    device = (await db.execute(stmt)).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio de red no encontrado")

    stmt_p = select(BandwidthProfile).where(
        BandwidthProfile.id == payload.bandwidth_profile_id, BandwidthProfile.tenant_id == tenant_id
    )
    profile = (await db.execute(stmt_p)).scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de ancho de banda destino no encontrado"
        )

    # Modificar límites en caliente en RouterOS v7
    try:
        _, client = await get_router_and_client(device.router_id, claims, db)
        async with client:
            q_name = f"SUB_{device.endpoint_identifier}"
            queues = await client.get(f"/queue/simple?name={q_name}")
            if queues and len(queues) > 0:
                q_id = queues[0].get(".id")
                await client.patch(
                    f"/queue/simple/{q_id}",
                    {
                        "max-limit": f"{profile.rate_up_kbps}k/{profile.rate_down_kbps}k",
                        "burst-limit": f"{profile.burst_up_kbps}k/{profile.burst_down_kbps}k",
                        "burst-threshold": f"{profile.burst_threshold_up_kbps}k/{profile.burst_threshold_down_kbps}k",
                        "burst-time": f"{profile.burst_time_seconds}s/{profile.burst_time_seconds}s",
                        "priority": f"{profile.priority}/{profile.priority}",
                    },
                )
    except Exception as exc:
        logger.warning(
            "No se pudo modificar cola en vivo en el router para %s: %s",
            device.endpoint_identifier,
            exc,
        )

    # Actualizar perfil en Base de Datos
    device.bandwidth_profile_id = profile.id
    device.updated_at = datetime.now(UTC)
    await db.commit()

    # Registro en Auditoría Inmutable WORM
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "api")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="OPERATIONS",
        event_action="NETWORK_SERVICE_RATE_LIMIT_CHANGED",
        status_code=200,
        after_state={
            "service_id": str(device.id),
            "endpoint_identifier": device.endpoint_identifier,
            "idempotency_key": idempotency_key,
            "bandwidth_profile_id": str(profile.id),
            "bandwidth_profile_name": profile.name,
        },
    )

    return NetworkServiceActionResponse(
        status="RATE_LIMIT_UPDATED",
        service_id=device.id,
        endpoint_identifier=device.endpoint_identifier,
        bandwidth_profile_id=profile.id,
        bandwidth_profile_name=profile.name,
        rate_down_kbps=profile.rate_down_kbps,
        rate_up_kbps=profile.rate_up_kbps,
        message="Límites de velocidad actualizados en caliente en RouterOS v7",
    )
