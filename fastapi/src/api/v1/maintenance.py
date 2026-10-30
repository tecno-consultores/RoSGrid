# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Ventanas de Mantenimiento Programadas (Silenciamiento de Alertas y Auto-Purga)."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.inventory import MaintenanceWindow
from src.schemas.inventory import (
    CreateMaintenanceWindowRequest,
    MaintenanceWindowResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


def _is_window_expired(window: Any, now_utc: datetime) -> bool:
    """Verifica de forma segura si un registro de ventana de mantenimiento ha superado su ends_at."""
    ends_at = getattr(window, "ends_at", None)
    if not isinstance(ends_at, datetime) or not hasattr(window, "starts_at") or not hasattr(window, "title"):
        return False
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=UTC)
    return ends_at <= now_utc


async def _delete_and_audit_expired_window(session: Any, window: Any, now_utc: datetime) -> None:
    """Elimina una ventana de mantenimiento vencida y deja constancia WORM en el AuditLog y en el log del sistema."""
    logger.info(
        "Eliminando automáticamente ventana de mantenimiento expirada id=%s title='%s' (ends_at=%s)",
        window.id,
        window.title,
        window.ends_at,
    )
    starts_at = getattr(window, "starts_at", None)
    ends_at = getattr(window, "ends_at", None)
    await write_audit_log(
        session=session,
        tenant_id=window.tenant_id,
        actor_user_id=getattr(window, "created_by", None),
        actor_username="system:maintenance-auto-purger",
        actor_role=SystemRoleEnum.SUPERADMIN_GLOBAL.value,
        actor_ip="127.0.0.1",
        actor_user_agent="RoSGrid-Maintenance-Auto-Purger/1.0",
        event_category="OPERATIONS",
        event_action="MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED",
        router_id=getattr(window, "router_id", None),
        before_state={
            "window_id": str(window.id),
            "title": window.title,
            "reason": getattr(window, "reason", ""),
            "target_tag": getattr(window, "target_tag", None),
            "starts_at": starts_at.isoformat() if isinstance(starts_at, datetime) else None,
            "ends_at": ends_at.isoformat() if isinstance(ends_at, datetime) else None,
        },
        after_state={
            "window_id": str(window.id),
            "status": "EXPIRED_AND_DELETED",
            "deleted_at": now_utc.isoformat(),
        },
    )
    await session.delete(window)


async def purge_expired_maintenance_windows(
    session: Any,
    tenant_id: uuid.UUID | None = None,
    commit: bool = False,
) -> int:
    """Busca y elimina todas las ventanas de mantenimiento cuya hora de finalización haya pasado."""
    now_utc = datetime.now(UTC)
    stmt = select(MaintenanceWindow).where(MaintenanceWindow.ends_at <= now_utc)
    if tenant_id is not None:
        stmt = stmt.where(MaintenanceWindow.tenant_id == tenant_id)
    result = await session.execute(stmt)
    candidates = result.scalars().all()
    expired = [w for w in candidates if _is_window_expired(w, now_utc)]
    for w in expired:
        await _delete_and_audit_expired_window(session, w, now_utc)
    if expired and commit:
        await session.commit()
    return len(expired)


def _apply_window_filters(
    query: Any,
    router_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    is_cancelled: bool | None = None,
) -> Any:
    if router_id is not None:
        query = query.where(MaintenanceWindow.router_id == router_id)
    if is_cancelled is not None:
        query = query.where(MaintenanceWindow.is_cancelled == is_cancelled)
    if is_active is not None:
        now_utc = datetime.now(UTC)
        if is_active:
            query = query.where(
                MaintenanceWindow.starts_at <= now_utc,
                MaintenanceWindow.ends_at >= now_utc,
                MaintenanceWindow.is_cancelled.is_(False),
            )
        else:
            query = query.where((MaintenanceWindow.ends_at < now_utc) | (MaintenanceWindow.is_cancelled.is_(True)))
    return query


@router.get("", response_model=list[MaintenanceWindowResponse])
@router.get("/windows", response_model=list[MaintenanceWindowResponse])
async def list_maintenance_windows(
    router_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    is_cancelled: bool | None = None,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[MaintenanceWindowResponse]:
    """Lista las ventanas de mantenimiento programadas del Tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    query = select(MaintenanceWindow).where(MaintenanceWindow.tenant_id == tenant_id)
    query = _apply_window_filters(query, router_id, is_active, is_cancelled)
    query = query.order_by(MaintenanceWindow.starts_at.desc())

    result = await db.execute(query)
    windows = list(result.scalars().all())
    now_utc = datetime.now(UTC)
    active_windows: list[Any] = []
    purged_any = False
    for w in windows:
        if _is_window_expired(w, now_utc):
            await _delete_and_audit_expired_window(db, w, now_utc)
            purged_any = True
        else:
            active_windows.append(w)
    if purged_any:
        await db.commit()
    return [MaintenanceWindowResponse.model_validate(w) for w in active_windows]


@router.post("", response_model=MaintenanceWindowResponse, status_code=status.HTTP_201_CREATED)
@router.post("/windows", response_model=MaintenanceWindowResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_window(
    payload: CreateMaintenanceWindowRequest,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> MaintenanceWindowResponse:
    """Programa una nueva ventana de mantenimiento para uno o varios routers o grupo por etiqueta."""
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de finalización debe ser posterior a la fecha de inicio",
        )

    target_router_ids: list[uuid.UUID] = []
    if payload.router_ids:
        target_router_ids.extend(payload.router_ids)
    elif payload.router_id:
        target_router_ids.append(payload.router_id)

    if not target_router_ids and not payload.target_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar al menos un router_id, una lista de routers o un target_tag",
        )

    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent")

    if target_router_ids:
        created_windows: list[MaintenanceWindow] = []
        for r_id in target_router_ids:
            window = MaintenanceWindow(
                tenant_id=tenant_id,
                title=payload.title.strip(),
                reason=payload.reason.strip(),
                router_id=r_id,
                target_tag=payload.target_tag.strip().lower() if payload.target_tag else None,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                suppress_alerts=payload.suppress_alerts,
                created_by=user_id,
            )
            db.add(window)
            created_windows.append(window)
        await db.flush()

        for w in created_windows:
            await write_audit_log(
                session=db,
                tenant_id=tenant_id,
                actor_user_id=user_id,
                actor_username=claims.get("sub", ""),
                actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
                actor_ip=ip_addr,
                actor_user_agent=ua,
                event_category="OPERATIONS",
                event_action="MAINTENANCE_WINDOW_CREATED",
                router_id=w.router_id,
                after_state={
                    "title": w.title,
                    "starts_at": w.starts_at.isoformat() if w.starts_at else None,
                    "ends_at": w.ends_at.isoformat() if w.ends_at else None,
                },
            )
        await db.commit()
        await db.refresh(created_windows[0])
        return MaintenanceWindowResponse.model_validate(created_windows[0])

    # Caso por etiqueta (target_tag) sin router individual específico
    window = MaintenanceWindow(
        tenant_id=tenant_id,
        title=payload.title.strip(),
        reason=payload.reason.strip(),
        router_id=None,
        target_tag=payload.target_tag.strip().lower() if payload.target_tag else None,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        suppress_alerts=payload.suppress_alerts,
        created_by=user_id,
    )
    db.add(window)
    await db.flush()

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="OPERATIONS",
        event_action="MAINTENANCE_WINDOW_CREATED",
        router_id=window.router_id,
        after_state={
            "title": window.title,
            "starts_at": window.starts_at.isoformat() if window.starts_at else None,
            "ends_at": window.ends_at.isoformat() if window.ends_at else None,
        },
    )
    await db.commit()
    await db.refresh(window)
    return MaintenanceWindowResponse.model_validate(window)


@router.post("/windows/{window_id}/cancel", response_model=MaintenanceWindowResponse)
@router.delete("/windows/{window_id}", response_model=MaintenanceWindowResponse)
@router.delete("/{window_id}", response_model=MaintenanceWindowResponse)
async def cancel_maintenance_window(
    window_id: uuid.UUID,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> MaintenanceWindowResponse:
    """Cancela de forma anticipada una ventana de mantenimiento y reactiva alertas."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])

    window = await db.get(MaintenanceWindow, window_id)
    if not window or window.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Ventana de mantenimiento no encontrada")

    window.is_cancelled = True

    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent")
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="OPERATIONS",
        event_action="MAINTENANCE_WINDOW_CANCELLED",
        router_id=window.router_id,
        after_state={"window_id": str(window.id), "is_cancelled": True},
    )
    await db.commit()
    await db.refresh(window)
    return MaintenanceWindowResponse.model_validate(window)
