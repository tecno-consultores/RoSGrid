# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Bandeja de Aprobación Maker-Checker: Segregación estricta de funciones y ejecución diferida con Safe Mode."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import (
    execute_safe_mutation,
    get_router_and_client,
)
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.models.operations import ApprovalRequest, ApprovalStatusEnum
from src.schemas.approvals import (
    ApprovalListResponse,
    ApprovalRequestResponse,
    ApproveRequestPayload,
    RejectRequestPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations/approvals", tags=["Maker-Checker Approvals"])

_GLOBAL_VIEW_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    SystemRoleEnum.TENANT_ADMIN.value,
    SystemRoleEnum.SUPERVISOR.value,
    SystemRoleEnum.SUPPORT_L3.value,
    SystemRoleEnum.AUDITOR.value,
}

_CHECKER_APPROVE_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
)


def _filter_approvals_by_role(claims: dict[str, Any], stmt: Any) -> Any:
    role = claims.get("rol")
    if role not in _GLOBAL_VIEW_ROLES:
        user_id = uuid.UUID(claims["sub"])
        stmt = stmt.where(ApprovalRequest.requested_by == user_id)
    return stmt


def _verify_pending_and_not_expired(approval: ApprovalRequest) -> None:
    if approval.status != ApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La solicitud no está pendiente (estado actual: {approval.status.value})",
        )
    now_utc = datetime.now(UTC)
    if approval.expires_at < now_utc:
        approval.status = ApprovalStatusEnum.EXPIRED
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La solicitud ha expirado y no puede ser aprobada",
        )


async def _execute_deferred_operation(
    client: MikrotikRestClient,
    approval: ApprovalRequest,
) -> Any:
    method = approval.ros_rest_method.upper()
    path = approval.ros_rest_path.strip("/")
    payload = approval.request_payload

    async def _action() -> Any:
        if method == "PUT":
            return await client.put(path, payload)
        elif method == "PATCH":
            return await client.patch(path, payload)
        elif method == "DELETE":
            return await client.delete(path)
        elif method == "POST":
            return await client.post(path, payload)
        raise ValueError(f"Método REST no soportado: {method}")

    action_name = "deferred_execution"
    return await execute_safe_mutation(
        client=client,
        menu=path,
        action=action_name,
        coro_fn=_action,
        item_id=payload.get(".id") if isinstance(payload, dict) else None,
        before_state=approval.previous_state_snapshot,
    )


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    status_filter: ApprovalStatusEnum | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ApprovalListResponse:
    """Lista solicitudes de cambio según el rol del usuario (SoD)."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(ApprovalRequest).where(ApprovalRequest.tenant_id == tenant_id)

    if status_filter:
        stmt = stmt.where(ApprovalRequest.status == status_filter)

    stmt = _filter_approvals_by_role(claims, stmt)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(ApprovalRequest.created_at)).limit(limit).offset(offset)
    records = (await db.execute(stmt)).scalars().all()

    items = [
        ApprovalRequestResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            router_id=r.router_id,
            action_type=r.action_type.value,
            status=r.status.value,
            summary=r.summary,
            requester_justification=r.requester_justification,
            ros_rest_method=r.ros_rest_method,
            ros_rest_path=r.ros_rest_path,
            request_payload=r.request_payload,
            previous_state_snapshot=r.previous_state_snapshot,
            requested_by=r.requested_by,
            reviewed_by=r.reviewed_by,
            review_comment=r.review_comment,
            expires_at=r.expires_at,
            reviewed_at=r.reviewed_at,
            executed_at=r.executed_at,
            execution_result=r.execution_result,
            created_at=r.created_at,
        )
        for r in records
    ]

    return ApprovalListResponse(total=total, items=items)


async def _execute_approval_lifecycle(
    client: MikrotikRestClient | None,
    approval: ApprovalRequest,
    now_utc: datetime,
) -> tuple[str, int]:
    try:
        if client:
            exec_res = await _execute_deferred_operation(client, approval)
            approval.execution_result = exec_res if isinstance(exec_res, dict) else {"response": exec_res}
        approval.status = ApprovalStatusEnum.APPROVED_AND_EXECUTED
        approval.executed_at = now_utc
        return "MAKER_CHECKER_APPROVED_AND_EXECUTED", 200
    except Exception as exc:
        logger.error("Error al ejecutar cambio diferido aprobado: %s", exc)
        approval.status = ApprovalStatusEnum.APPROVED_EXECUTION_FAILED
        approval.execution_result = {"error": str(exc)}
        return "MAKER_CHECKER_EXECUTION_FAILED", 500


async def _log_approval_audit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    claims: dict[str, Any],
    request: Request,
    checker_user_id: uuid.UUID,
    approval: ApprovalRequest,
    router_name: str | None,
    event_action: str,
    stat_code: int,
) -> None:
    err_msg = (
        str(approval.execution_result.get("error"))
        if (stat_code == 500 and approval.execution_result is not None)
        else None
    )
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "checker"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="MAKER_CHECKER",
        event_action=event_action,
        actor_user_id=checker_user_id,
        router_id=approval.router_id,
        router_display_name=router_name,
        ros_rest_method=approval.ros_rest_method,
        ros_rest_endpoint=approval.ros_rest_path,
        before_state=approval.previous_state_snapshot,
        after_state=approval.request_payload,
        status_code=stat_code,
        error_message=err_msg,
    )


@router.post("/{approval_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    approval_id: uuid.UUID,
    payload: ApproveRequestPayload,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_CHECKER_APPROVE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ApprovalRequestResponse:
    """Aprobación Checker: Aplica el cambio diferido en el MikroTik con Safe Mode."""
    tenant_id = uuid.UUID(claims["tid"])
    checker_user_id = uuid.UUID(claims["sub"])

    approval = await db.get(ApprovalRequest, approval_id)
    if not approval or approval.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Solicitud de aprobación no encontrada")

    # Inquebrantable SoD: Quien solicita NUNCA puede aprobar su propio cambio
    if approval.requested_by == checker_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Violación Maker-Checker: El solicitante no puede aprobar su propio cambio",
        )

    _verify_pending_and_not_expired(approval)

    client: MikrotikRestClient | None = None
    router_name: str | None = None
    if approval.router_id:
        r_obj, client = await get_router_and_client(approval.router_id, claims, db)
        router_name = r_obj.display_name

    now_utc = datetime.now(UTC)
    approval.reviewed_by = checker_user_id
    approval.reviewed_at = now_utc
    approval.review_comment = payload.review_comment

    event_action, stat_code = await _execute_approval_lifecycle(client, approval, now_utc)

    await _log_approval_audit(
        db, tenant_id, claims, request, checker_user_id, approval, router_name, event_action, stat_code
    )
    await db.commit()
    await db.refresh(approval)

    return ApprovalRequestResponse(
        id=approval.id,
        tenant_id=approval.tenant_id,
        router_id=approval.router_id,
        action_type=approval.action_type.value,
        status=approval.status.value,
        summary=approval.summary,
        requester_justification=approval.requester_justification,
        ros_rest_method=approval.ros_rest_method,
        ros_rest_path=approval.ros_rest_path,
        request_payload=approval.request_payload,
        previous_state_snapshot=approval.previous_state_snapshot,
        requested_by=approval.requested_by,
        reviewed_by=approval.reviewed_by,
        review_comment=approval.review_comment,
        expires_at=approval.expires_at,
        reviewed_at=approval.reviewed_at,
        executed_at=approval.executed_at,
        execution_result=approval.execution_result,
        created_at=approval.created_at,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    approval_id: uuid.UUID,
    payload: RejectRequestPayload,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_CHECKER_APPROVE_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ApprovalRequestResponse:
    """Rechaza una solicitud de cambio pendiente."""
    tenant_id = uuid.UUID(claims["tid"])
    checker_user_id = uuid.UUID(claims["sub"])

    approval = await db.get(ApprovalRequest, approval_id)
    if not approval or approval.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Solicitud de aprobación no encontrada")

    if approval.status != ApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La solicitud no está pendiente (estado actual: {approval.status.value})",
        )

    now_utc = datetime.now(UTC)
    approval.status = ApprovalStatusEnum.REJECTED
    approval.reviewed_by = checker_user_id
    approval.reviewed_at = now_utc
    approval.review_comment = payload.review_comment

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "checker"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="MAKER_CHECKER",
        event_action="MAKER_CHECKER_REJECTED",
        actor_user_id=checker_user_id,
        router_id=approval.router_id,
        status_code=200,
    )
    await db.commit()
    await db.refresh(approval)

    return ApprovalRequestResponse(
        id=approval.id,
        tenant_id=approval.tenant_id,
        router_id=approval.router_id,
        action_type=approval.action_type.value,
        status=approval.status.value,
        summary=approval.summary,
        requester_justification=approval.requester_justification,
        ros_rest_method=approval.ros_rest_method,
        ros_rest_path=approval.ros_rest_path,
        request_payload=approval.request_payload,
        previous_state_snapshot=approval.previous_state_snapshot,
        requested_by=approval.requested_by,
        reviewed_by=approval.reviewed_by,
        review_comment=approval.review_comment,
        expires_at=approval.expires_at,
        reviewed_at=approval.reviewed_at,
        executed_at=approval.executed_at,
        execution_result=approval.execution_result,
        created_at=approval.created_at,
    )
