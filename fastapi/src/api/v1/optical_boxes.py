# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Endpoints de Gestión de Cajas NAP (Optical Distribution Boxes / ODB / Infraestructura Pasiva).
Permite inventariar cajas en postes/fachadas, consultar matriz de puertos y clientes conectados.
"""

import csv
import io
import logging
import uuid
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user_claims, require_feature, require_roles
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.models.ipam import OpticalBox, SubscriberDevice
from src.schemas.ipam import (
    OpticalBoxCreate,
    OpticalBoxCsvCommitRequest,
    OpticalBoxCsvCommitResponse,
    OpticalBoxCsvDryRunResponse,
    OpticalBoxCsvRowPreview,
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
        actor_username=str(claims.get("preferred_username") or claims.get("username") or "system"),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="OPTICAL_BOX_CREATED",
        router_id=box.router_id,
        status_code=201,
        after_state={"box_id": str(box.id), "code": box.box_code, "capacity": box.capacity_ports},
    )
    await db.commit()

    res = OpticalBoxResponse.model_validate(box)
    res.occupied_ports_count = 0
    res.available_ports_count = box.capacity_ports
    return res


async def _load_optical_box_csv_context(
    db: AsyncSession, tenant_id: uuid.UUID
) -> tuple[dict[str, Router], dict[str, OpticalBox]]:
    r_res = await db.execute(select(Router).where(Router.tenant_id == tenant_id))
    routers_list = list(r_res.scalars().all())
    routers_by_key: dict[str, Router] = {}
    for r in routers_list:
        if r.display_name:
            routers_by_key[r.display_name.strip().lower()] = r
        if r.ros_identity:
            routers_by_key[r.ros_identity.strip().lower()] = r
        if r.api_base_url:
            clean_ip = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
            routers_by_key[clean_ip.strip().lower()] = r

    b_res = await db.execute(select(OpticalBox).where(OpticalBox.tenant_id == tenant_id))
    boxes_by_code = {b.box_code.strip().lower(): b for b in b_res.scalars().all() if b.box_code}
    return routers_by_key, boxes_by_code


def _validate_optical_box_csv_row(
    row: dict[str, Any],
    row_num: int,
    routers_by_key: dict[str, Router],
    boxes_by_code: dict[str, OpticalBox],
    seen_box_codes: set[str],
) -> OpticalBoxCsvRowPreview:
    errors: list[str] = []
    box_code = str(row.get("box_code") or "").strip()
    if not box_code:
        errors.append("El campo 'box_code' es obligatorio")
    elif len(box_code) > 64:
        errors.append("El campo 'box_code' excede 64 caracteres")
    elif box_code.lower() in seen_box_codes:
        errors.append(f"El código de caja '{box_code}' está duplicado en el mismo archivo CSV")
    else:
        seen_box_codes.add(box_code.lower())

    router_ref = str(row.get("router_name") or row.get("router_ip") or "").strip()
    matched_router = routers_by_key.get(router_ref.lower()) if router_ref else None
    if not router_ref:
        errors.append("El campo 'router_name' es obligatorio")
    elif not matched_router:
        errors.append(f"Router '{router_ref}' no encontrado en el inventario del tenant")

    raw_capacity = str(row.get("capacity_ports") or "16").strip()
    capacity = 16
    if raw_capacity:
        try:
            capacity = int(raw_capacity)
            if capacity < 1 or capacity > 64:
                errors.append("La capacidad de puertos debe estar entre 1 y 64")
        except ValueError:
            errors.append(f"Capacidad de puertos inválida '{raw_capacity}'")

    splitter = str(row.get("splitter_ratio") or "1:16").strip()
    if splitter not in {"1:2", "1:4", "1:8", "1:16", "1:32", "1:64"}:
        errors.append(f"Relación de splitter inválida '{splitter}' (use 1:2, 1:4, 1:8, 1:16, 1:32 o 1:64)")

    installation = str(row.get("installation_type") or "POLE").strip().upper()
    if installation not in {"POLE", "FACADE", "UNDERGROUND", "PEDESTAL", "MANHOLE", "INDOOR"}:
        errors.append(
            f"Tipo de instalación inválido '{installation}' (use POLE, FACADE, UNDERGROUND, PEDESTAL, MANHOLE o INDOOR)"
        )

    raw_power = str(row.get("input_power_dbm") or "").strip()
    power_val: Optional[float] = None
    if raw_power:
        try:
            power_val = float(raw_power)
        except ValueError:
            errors.append(f"Potencia óptica inválida '{raw_power}'")

    raw_lat = str(row.get("latitude") or "").strip()
    raw_lng = str(row.get("longitude") or "").strip()
    lat_val: float = 0.0
    lng_val: float = 0.0
    if not raw_lat or not raw_lng:
        errors.append("Los campos 'latitude' y 'longitude' son obligatorios")
    else:
        try:
            lat_val = float(raw_lat)
            lng_val = float(raw_lng)
            if not (-90.0 <= lat_val <= 90.0) or not (-180.0 <= lng_val <= 180.0):
                errors.append("Coordenadas GPS fuera de rango (-90..90 / -180..180)")
        except ValueError:
            errors.append("Latitud y longitud deben ser números decimales válidos")

    location = str(row.get("physical_location") or "").strip() or None
    if location and len(location) > 255:
        errors.append("El campo 'physical_location' excede 255 caracteres")

    is_update = bool(box_code and box_code.lower() in boxes_by_code)

    return OpticalBoxCsvRowPreview(
        row_number=row_num,
        box_code=box_code or f"NAP-{row_num}",
        router_name=router_ref,
        capacity_ports=capacity,
        splitter_ratio=splitter,
        installation_type=installation,
        input_power_dbm=power_val,
        latitude=lat_val,
        longitude=lng_val,
        physical_location=location,
        is_update=is_update,
        is_valid=len(errors) == 0,
        errors=errors,
    )


@optical_boxes_router.get("/template-csv")
async def download_optical_boxes_csv_template(
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> Response:
    """Descarga la plantilla CSV oficial RFC 4180 para importación masiva / Upsert de Cajas NAP."""
    headers = (
        "box_code,router_name,capacity_ports,splitter_ratio,installation_type,"
        "input_power_dbm,latitude,longitude,physical_location"
    )
    sample1 = 'NAP-NORTE-01,r1,16,1:16,POLE,-18.50,10.232347,-67.879893,"Poste P-14 Av. Principal"'
    sample2 = 'NAP-NORTE-02,r1,8,1:8,FACADE,-19.20,10.233100,-67.880500,"Fachada Edif. Centro"'
    content = f"\ufeff{headers}\r\n{sample1}\r\n{sample2}\r\n"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="rosgrid-cajas-nap-plantilla.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@optical_boxes_router.post("/import-csv/dry-run", response_model=OpticalBoxCsvDryRunResponse)
async def import_optical_boxes_csv_dry_run(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> OpticalBoxCsvDryRunResponse:
    """Paso 1: Validación en seco de archivo CSV para carga masiva / Upsert de Cajas NAP (máximo 500 filas)."""
    tenant_id = get_tenant_id(claims)
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo permitido de 2 MB")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="El archivo debe tener codificación UTF-8 válida") from exc

    routers_by_key, boxes_by_code = await _load_optical_box_csv_context(db, tenant_id)
    reader = csv.DictReader(io.StringIO(decoded))
    previews: list[OpticalBoxCsvRowPreview] = []
    seen_codes: set[str] = set()
    row_num = 1

    for row in reader:
        row_num += 1
        if row_num > 501:
            raise HTTPException(status_code=400, detail="El archivo excede el límite de 500 filas")
        preview = _validate_optical_box_csv_row(row, row_num, routers_by_key, boxes_by_code, seen_codes)
        previews.append(preview)

    valid_count = sum(1 for p in previews if p.is_valid)
    invalid_count = len(previews) - valid_count
    return OpticalBoxCsvDryRunResponse(
        total_rows=len(previews),
        valid_rows_count=valid_count,
        invalid_rows_count=invalid_count,
        can_proceed=invalid_count == 0 and valid_count > 0,
        rows=previews,
    )


@optical_boxes_router.post("/import-csv/commit", response_model=OpticalBoxCsvCommitResponse)
async def import_optical_boxes_csv_commit(
    request: Request,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> OpticalBoxCsvCommitResponse:
    """Paso 2: Confirmación e inserción/actualización (Upsert) transaccional de Cajas NAP con auditoría WORM."""
    tenant_id = get_tenant_id(claims)
    routers_by_key, boxes_by_code = await _load_optical_box_csv_context(db, tenant_id)

    content_type = request.headers.get("content-type", "")
    valid_rows: list[OpticalBoxCsvRowPreview] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(status_code=400, detail="Debe proporcionar un archivo CSV en el campo 'file'")
        content = await upload.read()
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="El archivo debe tener codificación UTF-8 válida") from exc
        reader = csv.DictReader(io.StringIO(decoded))
        seen_codes: set[str] = set()
        for idx, row in enumerate(reader, start=2):
            p = _validate_optical_box_csv_row(row, idx, routers_by_key, boxes_by_code, seen_codes)
            if p.is_valid:
                valid_rows.append(p)
    else:
        body = await request.json()
        payload = OpticalBoxCsvCommitRequest.model_validate(body)
        valid_rows = [r for r in payload.rows if r.is_valid]

    if not valid_rows:
        raise HTTPException(status_code=400, detail="No hay filas válidas para importar")

    box_ids: list[uuid.UUID] = []
    imported_count = 0
    updated_count = 0

    for item in valid_rows:
        matched_router = routers_by_key.get(item.router_name.strip().lower())
        if not matched_router:
            continue
        code_key = item.box_code.strip().lower()
        existing_box = boxes_by_code.get(code_key)
        if existing_box:
            existing_box.router_id = matched_router.id
            existing_box.capacity_ports = item.capacity_ports
            existing_box.splitter_ratio = item.splitter_ratio
            existing_box.installation_type = item.installation_type
            if item.input_power_dbm is not None:
                existing_box.input_power_dbm = Decimal(str(item.input_power_dbm))
            existing_box.latitude = Decimal(str(item.latitude))
            existing_box.longitude = Decimal(str(item.longitude))
            if item.physical_location is not None:
                existing_box.physical_location = item.physical_location
            box_ids.append(existing_box.id)
            updated_count += 1
        else:
            new_box = OpticalBox(
                tenant_id=tenant_id,
                router_id=matched_router.id,
                box_code=item.box_code.strip(),
                capacity_ports=item.capacity_ports,
                splitter_ratio=item.splitter_ratio,
                installation_type=item.installation_type,
                input_power_dbm=Decimal(str(item.input_power_dbm)) if item.input_power_dbm is not None else None,
                latitude=Decimal(str(item.latitude)),
                longitude=Decimal(str(item.longitude)),
                physical_location=item.physical_location,
                status="ACTIVE",
            )
            db.add(new_box)
            await db.flush()
            boxes_by_code[code_key] = new_box
            box_ids.append(new_box.id)
            imported_count += 1

    await db.flush()
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])) if claims.get("sub") else None,
        actor_username=str(claims.get("preferred_username") or claims.get("username") or "admin"),
        actor_role=str(claims.get("rol") or SystemRoleEnum.TENANT_ADMIN.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="INVENTORY",
        event_action="OPTICAL_BOXES_CSV_BULK_IMPORTED",
        after_state={"imported_count": imported_count, "updated_count": updated_count},
        status_code=201,
    )
    await db.commit()

    return OpticalBoxCsvCommitResponse(
        imported_count=imported_count,
        updated_count=updated_count,
        box_ids=box_ids,
        message=f"Se procesaron {imported_count + updated_count} Cajas NAP exitosamente ({imported_count} nuevas, {updated_count} actualizadas).",
    )


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

    # Obtener suscriptores conectados con relación IPv4 pre-cargada
    stmt_subs = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.ipv4_address))
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

    base_data = OpticalBoxResponse.model_validate(box).model_dump()
    base_data["occupied_ports_count"] = occupied_count
    base_data["available_ports_count"] = available_count
    return OpticalBoxDetailResponse(
        **base_data,
        ports=ports,
        subscribers=sub_responses,
    )


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
        actor_username=str(claims.get("preferred_username") or claims.get("username") or "system"),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="OPTICAL_BOX_DELETED",
        router_id=box.router_id,
        status_code=204,
        after_state={"box_id": str(box_id), "code": box.box_code},
    )
    await db.commit()
