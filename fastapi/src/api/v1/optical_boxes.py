# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Gestión de Cajas NAP (Optical Distribution Boxes / ODB / Infraestructura Pasiva).
Permite inventariar cajas en postes/fachadas, consultar matriz de puertos y clientes conectados.
"""

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_feature, require_roles
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.models.ipam import OpticalBox, SubscriberDevice
from src.schemas.ipam import (
    OpticalBoxCreate,
    OpticalBoxDetailResponse,
    OpticalBoxPortStatus,
    OpticalBoxResponse,
    OpticalBoxUpdate,
    SubscriberDeviceResponse,
)

logger = logging.getLogger(__name__)

optical_boxes_router = APIRouter(
    prefix="/optical-boxes",
    tags=["Optical Distribution Boxes / Cajas NAP"],
    dependencies=[Depends(require_feature("isp_module_enabled"))],
)


def get_tenant_id(claims: dict[str, Any]) -> uuid.UUID:
    tid = claims.get("tid") or claims.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant ID no encontrado en sesión")
    return uuid.UUID(str(tid))


@optical_boxes_router.get("", response_model=list[OpticalBoxResponse])
async def list_optical_boxes(
    router_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista las Cajas NAP del tenant con cálculo dinámico de puertos libres y ocupados."""
    tenant_id = get_tenant_id(claims)

    stmt = select(OpticalBox).where(OpticalBox.tenant_id == tenant_id)
    if router_id:
        stmt = stmt.where(OpticalBox.router_id == router_id)
    if status_filter:
        stmt = stmt.where(OpticalBox.status == status_filter)

    stmt = stmt.order_by(OpticalBox.box_code.asc())
    boxes = list((await db.execute(stmt)).scalars().all())

    # Calcular ocupación por caja
    stmt_counts = (
        select(SubscriberDevice.optical_box_id, func.count(SubscriberDevice.id).label("cnt"))
        .where(
            SubscriberDevice.tenant_id == tenant_id,
            SubscriberDevice.optical_box_id.isnot(None),
        )
        .group_by(SubscriberDevice.optical_box_id)
    )
    counts_map = dict((await db.execute(stmt_counts)).all())

    response: list[OpticalBoxResponse] = []
    for b in boxes:
        occupied = counts_map.get(b.id, 0)
        available = max(0, b.capacity_ports - occupied)
        res_item = OpticalBoxResponse.model_validate(b)
        res_item.occupied_ports_count = occupied
        res_item.available_ports_count = available
        response.append(res_item)

    return response


@optical_boxes_router.post("", response_model=OpticalBoxResponse, status_code=status.HTTP_201_CREATED)
async def create_optical_box(
    payload: OpticalBoxCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> Any:
    """Registra una nueva Caja NAP en la red pasiva FTTH."""
    tenant_id = get_tenant_id(claims)

    # Validar existencia del router
    stmt_r = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(stmt_r)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router asignado no encontrado")

    # Validar unicidad del código de caja en el tenant
    stmt_check = select(OpticalBox).where(
        OpticalBox.tenant_id == tenant_id,
        OpticalBox.box_code == payload.box_code,
    )
    if (await db.execute(stmt_check)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una Caja NAP con este código")

    box = OpticalBox(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        box_code=payload.box_code,
        brand=payload.brand,
        model=payload.model,
        capacity_ports=payload.capacity_ports,
        splitter_ratio=payload.splitter_ratio,
        installation_type=payload.installation_type,
        physical_location=payload.physical_location,
        input_power_dbm=payload.input_power_dbm,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(box)
    await db.commit()
    await db.refresh(box)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="OPTICAL_BOX_CREATED",
        status_code=201,
        after_state={"box_id": str(box.id), "code": box.box_code, "capacity": box.capacity_ports},
    )

    res = OpticalBoxResponse.model_validate(box)
    res.occupied_ports_count = 0
    res.available_ports_count = box.capacity_ports
    return res


@optical_boxes_router.get("/{box_id}", response_model=OpticalBoxDetailResponse)
async def get_optical_box_detail(
    box_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Obtiene el detalle completo de una Caja NAP con la matriz de puertos 1..N y abonados conectados."""
    tenant_id = get_tenant_id(claims)

    stmt_box = select(OpticalBox).where(OpticalBox.id == box_id, OpticalBox.tenant_id == tenant_id)
    box = (await db.execute(stmt_box)).scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caja NAP no encontrada")

    # Obtener suscriptores conectados
    stmt_subs = (
        select(SubscriberDevice)
        .where(
            SubscriberDevice.tenant_id == tenant_id,
            SubscriberDevice.optical_box_id == box_id,
        )
        .order_by(SubscriberDevice.optical_box_port.asc().nulls_last())
    )
    subs = list((await db.execute(stmt_subs)).scalars().all())

    # Construir mapa de puerto a suscriptor
    port_map: dict[int, SubscriberDevice] = {}
    for s in subs:
        if s.optical_box_port and s.optical_box_port > 0:
            port_map[s.optical_box_port] = s

    ports: list[OpticalBoxPortStatus] = []
    for port_num in range(1, box.capacity_ports + 1):
        if port_num in port_map:
            sub = port_map[port_num]
            ports.append(
                OpticalBoxPortStatus(
                    port_number=port_num,
                    is_occupied=True,
                    subscriber_id=sub.id,
                    subscriber_identifier=sub.endpoint_identifier or sub.device_serial,
                    assigned_ipv4=sub.assigned_ipv4,
                    reachability_status=sub.last_reachability_status,
                    rx_power_dbm=sub.rx_optical_power_dbm,
                )
            )
        else:
            ports.append(
                OpticalBoxPortStatus(
                    port_number=port_num,
                    is_occupied=False,
                    reachability_status="FREE",
                )
            )

    sub_responses = [SubscriberDeviceResponse.model_validate(s) for s in subs]
    occupied_count = len(port_map)
    available_count = max(0, box.capacity_ports - occupied_count)

    detail = OpticalBoxDetailResponse.model_validate(box)
    detail.occupied_ports_count = occupied_count
    detail.available_ports_count = available_count
    detail.ports = ports
    detail.subscribers = sub_responses
    return detail


@optical_boxes_router.patch("/{box_id}", response_model=OpticalBoxResponse)
async def update_optical_box(
    box_id: uuid.UUID,
    payload: OpticalBoxUpdate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> Any:
    """Actualiza los parámetros físicos o coordenadas de una Caja NAP."""
    tenant_id = get_tenant_id(claims)

    stmt = select(OpticalBox).where(OpticalBox.id == box_id, OpticalBox.tenant_id == tenant_id)
    box = (await db.execute(stmt)).scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caja NAP no encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(box, field, val)

    await db.commit()
    await db.refresh(box)

    # Calcular ocupación
    stmt_count = select(func.count(SubscriberDevice.id)).where(
        SubscriberDevice.tenant_id == tenant_id,
        SubscriberDevice.optical_box_id == box_id,
    )
    occupied = (await db.execute(stmt_count)).scalar() or 0

    res = OpticalBoxResponse.model_validate(box)
    res.occupied_ports_count = occupied
    res.available_ports_count = max(0, box.capacity_ports - occupied)
    return res


@optical_boxes_router.delete("/{box_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_optical_box(
    box_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
        )
    ),
) -> None:
    """Elimina una Caja NAP desvinculando de forma segura los abonados enlazados."""
    tenant_id = get_tenant_id(claims)

    stmt = select(OpticalBox).where(OpticalBox.id == box_id, OpticalBox.tenant_id == tenant_id)
    box = (await db.execute(stmt)).scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caja NAP no encontrada")

    await db.delete(box)
    await db.commit()

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="OPTICAL_BOX_DELETED",
        status_code=204,
        after_state={"box_id": str(box_id), "code": box.box_code},
    )
