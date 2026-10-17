# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Consola Forense de Auditoría Inmutable, Verificación WORM y Exportación Firmada."""

import csv
import hashlib
import io
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.core.audit import GENESIS_AUDIT_HASH, compute_audit_record_hash
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.operations import AuditLog
from src.schemas.audit import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditVerifyIntegrityResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit/logs", tags=["Audit Console"])

_AUDITOR_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.AUDITOR,
)


def _apply_audit_filters(
    stmt: Any,
    actor_user_id: uuid.UUID | None,
    router_id: uuid.UUID | None,
    category: str | None,
    action: str | None,
) -> Any:
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if router_id:
        stmt = stmt.where(AuditLog.router_id == router_id)
    if category:
        stmt = stmt.where(AuditLog.event_category == category)
    if action:
        stmt = stmt.where(AuditLog.event_action == action)
    return stmt


def _apply_date_filters(
    stmt: Any,
    date_from: datetime | None,
    date_to: datetime | None,
    status_code: int | None,
) -> Any:
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)
    if status_code:
        stmt = stmt.where(AuditLog.status_code == status_code)
    return stmt


def _verify_single_audit_record(record: AuditLog, expected_prev: str) -> bool:
    if record.prev_record_hash != expected_prev:
        return False
    payload = {
        "tenant_id": str(record.tenant_id),
        "actor_user_id": str(record.actor_user_id) if record.actor_user_id else None,
        "actor_username": record.actor_username,
        "event_category": record.event_category,
        "event_action": record.event_action,
        "router_id": str(record.router_id) if record.router_id else None,
        "status_code": record.status_code,
        "before_state": record.before_state,
        "after_state": record.after_state,
    }
    rec_hash = compute_audit_record_hash(expected_prev, payload)
    return rec_hash == record.record_sha256_hash


def _build_export_csv(records: list[AuditLog]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "created_at",
            "actor_username",
            "actor_role",
            "actor_ip",
            "event_category",
            "event_action",
            "router_display_name",
            "status_code",
            "record_sha256_hash",
        ]
    )
    for r in records:
        writer.writerow(
            [
                str(r.id),
                r.created_at.isoformat(),
                r.actor_username,
                r.actor_role.value if hasattr(r.actor_role, "value") else str(r.actor_role),
                r.actor_ip,
                r.event_category,
                r.event_action,
                r.router_display_name or "",
                r.status_code,
                r.record_sha256_hash,
            ]
        )
    return output.getvalue()


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    actor_user_id: uuid.UUID | None = Query(default=None),
    router_id: uuid.UUID | None = Query(default=None),
    category: str | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    status_code: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    claims: dict[str, Any] = Depends(require_roles(*_AUDITOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> AuditLogListResponse:
    """Consulta la consola de auditoría inmutable con filtros forenses avanzados."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
    stmt = _apply_audit_filters(stmt, actor_user_id, router_id, category, action)
    stmt = _apply_date_filters(stmt, date_from, date_to, status_code)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(limit).offset(offset)
    records = (await db.execute(stmt)).scalars().all()

    items = [
        AuditLogResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            actor_user_id=r.actor_user_id,
            actor_username=r.actor_username,
            actor_role=r.actor_role.value if hasattr(r.actor_role, "value") else str(r.actor_role),
            actor_ip=str(r.actor_ip) if r.actor_ip is not None else "",
            actor_user_agent=r.actor_user_agent,
            event_category=r.event_category,
            event_action=r.event_action,
            router_id=r.router_id,
            router_display_name=r.router_display_name,
            ros_rest_method=r.ros_rest_method,
            ros_rest_endpoint=r.ros_rest_endpoint,
            idempotency_key=r.idempotency_key,
            before_state=r.before_state,
            after_state=r.after_state,
            status_code=r.status_code,
            error_message=r.error_message,
            prev_record_hash=r.prev_record_hash,
            record_sha256_hash=r.record_sha256_hash,
            created_at=r.created_at,
        )
        for r in records
    ]
    return AuditLogListResponse(total=total, limit=limit, offset=offset, items=items)


@router.post("/verify-integrity", response_model=AuditVerifyIntegrityResponse)
async def verify_audit_integrity(
    claims: dict[str, Any] = Depends(require_roles(*_AUDITOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> AuditVerifyIntegrityResponse:
    """Verifica matemáticamente la integridad de la cadena WORM encadenada por SHA-256."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = (
        select(AuditLog).where(AuditLog.tenant_id == tenant_id).order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
    )
    records = (await db.execute(stmt)).scalars().all()

    expected_prev = GENESIS_AUDIT_HASH
    verified_count = 0

    for rec in records:
        is_intact = _verify_single_audit_record(rec, expected_prev)
        if not is_intact:
            logger.critical("Violación forense WORM en registro de auditoría ID: %s", rec.id)
            return AuditVerifyIntegrityResponse(
                integrity_status="COMPROMISED",
                verified_records_count=verified_count,
                corrupted_record_id=rec.id,
                message=f"Violación criptográfica detectada en el registro de auditoría {rec.id}",
            )
        expected_prev = rec.record_sha256_hash
        verified_count += 1

    return AuditVerifyIntegrityResponse(
        integrity_status="VERIFIED_INTACT",
        verified_records_count=verified_count,
        message=f"Cadena WORM 100% íntegra y verificada ({verified_count} registros evaluados)",
    )


@router.get("/export")
async def export_audit_logs(
    export_format: str = Query(default="json", alias="format"),
    actor_user_id: uuid.UUID | None = Query(default=None),
    router_id: uuid.UUID | None = Query(default=None),
    category: str | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    status_code: int | None = Query(default=None),
    claims: dict[str, Any] = Depends(require_roles(*_AUDITOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Response:
    """Exporta el rango filtrado en formato CSV o JSON firmado con su hash SHA-256 en cabecera."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
    stmt = _apply_audit_filters(stmt, actor_user_id, router_id, category, action)
    stmt = _apply_date_filters(stmt, date_from, date_to, status_code)
    stmt = stmt.order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(5000)
    records = list((await db.execute(stmt)).scalars().all())

    if export_format.lower() == "csv":
        content_str = _build_export_csv(records)
        media_type = "text/csv; charset=utf-8"
        filename = f"audit_export_{tenant_id}.csv"
    else:
        raw_list = [
            {
                "id": str(r.id),
                "created_at": r.created_at.isoformat(),
                "actor_username": r.actor_username,
                "event_category": r.event_category,
                "event_action": r.event_action,
                "status_code": r.status_code,
                "record_sha256_hash": r.record_sha256_hash,
            }
            for r in records
        ]
        content_str = json.dumps(raw_list, indent=2)
        media_type = "application/json"
        filename = f"audit_export_{tenant_id}.json"

    digest = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Audit-Digest": digest,
    }
    return Response(content=content_str, media_type=media_type, headers=headers)
