# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Bandeja de Aprobación Maker-Checker: Segregación estricta de funciones y ejecución diferida con Safe Mode."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.bulk_and_updates import execute_bulk_job_on_fleet
from src.api.v1.webfig_common import (
    execute_safe_mutation,
    get_router_and_client,
    invalidate_webfig_cache,
    publish_maker_checker_event,
)
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum, User
from src.models.inventory import Router
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    BulkJob,
    BulkJobStatusEnum,
    CriticalActionTypeEnum,
)
from src.redis_layer.client import get_redis_client
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
    if path.startswith("rest/"):
        path = path[5:].strip("/")
    payload = approval.request_payload if isinstance(approval.request_payload, dict) else {}
    keep_dot_id = method == "POST" and (path.endswith("/remove") or "/remove" in path or "mcp_tool" in payload)
    clean_payload = (
        {k: v for k, v in payload.items() if k not in ("mcp_tool", "pppoe_username")}
        if keep_dot_id
        else {k: v for k, v in payload.items() if k != ".id"}
    )

    menu_path = path
    inferred_id = (
        str(payload.get(".id")).strip()
        if isinstance(payload, dict) and payload.get(".id") is not None and str(payload.get(".id")).strip()
        else None
    )
    if method in ("PATCH", "DELETE") and "/" in path:
        parts = path.rsplit("/", 1)
        if parts[1].startswith("*") or parts[1].isdigit():
            menu_path = parts[0]
            inferred_id = inferred_id or parts[1]

    target_path = f"{menu_path}/{inferred_id}" if method in ("PATCH", "DELETE") and inferred_id else path

    async def _action() -> Any:
        if method == "PUT":
            return await client.put(f"/{target_path}", clean_payload)
        elif method == "PATCH":
            return await client.patch(f"/{target_path}", clean_payload)
        elif method == "DELETE":
            return await client.delete(f"/{target_path}")
        elif method == "POST":
            return await client.post(f"/{target_path}", clean_payload)
        raise ValueError(f"Método REST no soportado: {method}")

    action_name = "create" if method == "PUT" else ("delete" if method == "DELETE" else "set")
    return await execute_safe_mutation(
        client=client,
        menu=menu_path,
        action=action_name,
        coro_fn=_action,
        item_id=inferred_id,
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

    users_map: dict[uuid.UUID, User] = {}
    routers_map: dict[uuid.UUID, Router] = {}
    if type(db) is AsyncSession and records:
        req_uids = {r.requested_by for r in records if r.requested_by}
        req_rids = {r.router_id for r in records if r.router_id}
        if req_uids:
            u_rows = (await db.execute(select(User).where(User.id.in_(req_uids)))).scalars().all()
            users_map = {u.id: u for u in u_rows}
        if req_rids:
            rt_rows = (await db.execute(select(Router).where(Router.id.in_(req_rids)))).scalars().all()
            routers_map = {rt.id: rt for rt in rt_rows}

    items: list[ApprovalRequestResponse] = []
    for r in records:
        req_username: str | None = None
        req_role: str | None = None
        r_name: str | None = None
        if r.requested_by in users_map:
            u_cached = users_map[r.requested_by]
            req_username = u_cached.username
            req_role = u_cached.role.value if hasattr(u_cached.role, "value") else str(u_cached.role)
        if r.router_id and r.router_id in routers_map:
            r_name = routers_map[r.router_id].display_name
        if type(db) is not AsyncSession:
            try:
                u_obj = await db.get(User, r.requested_by)
                if isinstance(u_obj, User):
                    req_username = u_obj.username
                    req_role = u_obj.role.value if hasattr(u_obj.role, "value") else str(u_obj.role)
                if r.router_id:
                    rt_obj = await db.get(Router, r.router_id)
                    if isinstance(rt_obj, Router):
                        r_name = rt_obj.display_name
            except Exception as exc:
                logger.debug("No se pudo resolver metadatos de solicitud en sesión mock: %s", exc)

        items.append(
            ApprovalRequestResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                router_id=r.router_id,
                router_name=r_name,
                action_type=r.action_type.value,
                status=r.status.value,
                summary=r.summary,
                requester_justification=r.requester_justification,
                ros_rest_method=r.ros_rest_method,
                ros_rest_path=r.ros_rest_path,
                request_payload=r.request_payload,
                previous_state_snapshot=r.previous_state_snapshot,
                requested_by=r.requested_by,
                requested_by_username=req_username,
                requested_by_role=req_role,
                reviewed_by=r.reviewed_by,
                review_comment=r.review_comment,
                expires_at=r.expires_at,
                reviewed_at=r.reviewed_at,
                executed_at=r.executed_at,
                execution_result=r.execution_result,
                created_at=r.created_at,
            )
        )

    return ApprovalListResponse(total=total, items=items)


async def _execute_mcp_deferred_tool(
    approval: ApprovalRequest,
    claims: dict[str, Any],
    db: AsyncSession,
    tenant_id: uuid.UUID,
    checker_user_id: uuid.UUID,
) -> dict[str, Any] | None:
    payload = approval.request_payload if isinstance(approval.request_payload, dict) else {}
    mcp_tool = payload.get("mcp_tool")
    if not mcp_tool:
        return None
    ik = str(payload.get("idempotency_key") or uuid.uuid4())
    if mcp_tool == "rosgrid_isolate_subscriber":
        from src.api.v1.network_services import isolate_network_service

        sub_id = uuid.UUID(str(payload["subscriber_device_id"]))
        res = await isolate_network_service(sub_id, ik, db, claims)
        return res.model_dump()
    if mcp_tool == "rosgrid_restore_subscriber":
        from src.api.v1.network_services import restore_network_service

        sub_id = uuid.UUID(str(payload["subscriber_device_id"]))
        res = await restore_network_service(sub_id, ik, db, claims)
        return res.model_dump()
    if mcp_tool in ("rosgrid_change_rate_limit", "rosgrid_change_subscriber_rate_limit"):
        from src.api.v1.network_services import change_network_service_rate_limit
        from src.schemas.network_services import ChangeRateLimitRequest

        sub_id = uuid.UUID(str(payload["subscriber_device_id"]))
        prof_id = uuid.UUID(str(payload["bandwidth_profile_id"]))
        req = ChangeRateLimitRequest(bandwidth_profile_id=prof_id)
        res = await change_network_service_rate_limit(sub_id, req, ik, db, claims)
        return res.model_dump()
    if mcp_tool == "rosgrid_execute_poe_aware_upgrade":
        from src.api.v1.bulk_and_updates import _process_upgrade_stages, _resolve_upgrade_stages
        from src.schemas.bulk_and_updates import RosUpdateExecuteRequest

        rids = [uuid.UUID(str(x)) for x in payload.get("router_ids", [])]
        upg_req = RosUpdateExecuteRequest(
            router_ids=rids,
            auto_upgrade_firmware=bool(payload.get("auto_upgrade_firmware", True)),
            poe_aware=bool(payload.get("poe_aware", True)),
            safety_stop_threshold_percent=float(payload.get("safety_stop_threshold_percent", 1.0)),
        )
        stages = await _resolve_upgrade_stages(tenant_id, upg_req.router_ids, upg_req.poe_aware)
        results, stopped = await _process_upgrade_stages(stages, upg_req, claims, db, tenant_id, checker_user_id)
        return {
            "status": "SAFETY_STOPPED" if stopped else "COMPLETED",
            "safety_stop_triggered": stopped,
            "processed_count": len(results),
            "results": results,
        }
    return None


async def _execute_approval_lifecycle(
    client: MikrotikRestClient | None,
    approval: ApprovalRequest,
    now_utc: datetime,
    claims: dict[str, Any] | None = None,
    db: AsyncSession | None = None,
    tenant_id: uuid.UUID | None = None,
    checker_user_id: uuid.UUID | None = None,
) -> tuple[str, int]:
    try:
        if claims and db and tenant_id and checker_user_id:
            mcp_res = await _execute_mcp_deferred_tool(approval, claims, db, tenant_id, checker_user_id)
            if mcp_res is not None:
                approval.execution_result = mcp_res
                approval.status = ApprovalStatusEnum.APPROVED_AND_EXECUTED
                approval.executed_at = now_utc
                return "MAKER_CHECKER_APPROVED_AND_EXECUTED", 200
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
    await publish_maker_checker_event(
        tenant_id=tenant_id,
        event_name="MAKER_CHECKER_RESOLVED",
        approval_id=approval.id,
        summary=approval.summary,
        router_id=approval.router_id,
        resolution_status=approval.status.value if hasattr(approval.status, "value") else str(approval.status),
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

    from src.api.v1.vault import _verify_admin_totp

    checker_user = await db.get(User, checker_user_id) if type(db) is AsyncSession else None
    if isinstance(checker_user, User) and getattr(checker_user, "totp_enabled", False):
        if not payload.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código 2FA TOTP requerido para aprobar cambios críticos en la red",
            )
        await _verify_admin_totp(db, tenant_id, checker_user_id, payload.totp_code)
    elif payload.totp_code:
        await _verify_admin_totp(db, tenant_id, checker_user_id, payload.totp_code)

    if type(db) is AsyncSession:
        stmt_lock = (
            select(ApprovalRequest)
            .where(ApprovalRequest.id == approval_id, ApprovalRequest.tenant_id == tenant_id)
            .with_for_update()
        )
        approval = (await db.execute(stmt_lock)).scalar_one_or_none()
    else:
        approval = await db.get(ApprovalRequest, approval_id)
    if not approval or approval.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Solicitud de aprobación no encontrada")

    # Inquebrantable SoD: Quien solicita NUNCA puede aprobar su propio cambio (excepto SUPERADMIN_GLOBAL en entorno único)
    if approval.requested_by == checker_user_id and claims.get("rol") != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Violación Maker-Checker: El solicitante no puede aprobar su propio cambio",
        )

    try:
        _verify_pending_and_not_expired(approval)
    except HTTPException:
        if approval.status == ApprovalStatusEnum.EXPIRED:
            await db.commit()
        raise

    client: MikrotikRestClient | None = None
    router_name: str | None = None
    if approval.router_id:
        r_obj, client = await get_router_and_client(approval.router_id, claims, db)
        router_name = r_obj.display_name

    now_utc = datetime.now(UTC)
    approval.reviewed_by = None if approval.requested_by == checker_user_id else checker_user_id
    approval.reviewed_at = now_utc
    approval.review_comment = payload.review_comment

    is_mcp_upgrade = (
        isinstance(approval.request_payload, dict)
        and approval.request_payload.get("mcp_tool") == "rosgrid_execute_poe_aware_upgrade"
    )
    try:
        if approval.action_type == CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION and not is_mcp_upgrade:
            stmt_job = select(BulkJob).where(BulkJob.approval_request_id == approval.id)
            job_obj = (await db.execute(stmt_job)).scalar_one_or_none()
            if job_obj:
                job_obj = await execute_bulk_job_on_fleet(job_obj, db, claims)
                if job_obj.status in (BulkJobStatusEnum.COMPLETED, BulkJobStatusEnum.PARTIAL_FAILURE):
                    approval.status = ApprovalStatusEnum.APPROVED_AND_EXECUTED
                    approval.execution_result = {
                        "succeeded_count": job_obj.succeeded_count,
                        "failed_count": job_obj.failed_count,
                        "total_routers": job_obj.total_routers,
                        "job_status": job_obj.status.value,
                    }
                    event_action = "MAKER_CHECKER_APPROVED_AND_EXECUTED"
                    stat_code = 200
                else:
                    approval.status = ApprovalStatusEnum.APPROVED_EXECUTION_FAILED
                    approval.execution_result = {
                        "succeeded_count": job_obj.succeeded_count,
                        "failed_count": job_obj.failed_count,
                        "job_status": job_obj.status.value,
                        "error": "Falló la ejecución de la plantilla en los routers objetivo",
                    }
                    event_action = "MAKER_CHECKER_EXECUTION_FAILED"
                    stat_code = 500
            else:
                approval.status = ApprovalStatusEnum.APPROVED_AND_EXECUTED
                approval.execution_result = {"status": "NO_BULK_JOB_ATTACHED"}
                event_action = "MAKER_CHECKER_APPROVED_AND_EXECUTED"
                stat_code = 200
            approval.executed_at = now_utc
        else:
            event_action, stat_code = await _execute_approval_lifecycle(
                client, approval, now_utc, claims=claims, db=db, tenant_id=tenant_id, checker_user_id=checker_user_id
            )
    finally:
        if client is not None:
            await client.close()

    await _log_approval_audit(
        db, tenant_id, claims, request, checker_user_id, approval, router_name, event_action, stat_code
    )
    await db.commit()
    await db.refresh(approval)

    if approval.router_id and approval.ros_rest_path:
        try:
            redis = get_redis_client()
            clean_p = approval.ros_rest_path.strip("/")
            if clean_p.startswith("rest/"):
                clean_p = clean_p[5:].strip("/")
            await invalidate_webfig_cache(redis, tenant_id, approval.router_id, f"/{clean_p}")
            if "/" in clean_p:
                await invalidate_webfig_cache(redis, tenant_id, approval.router_id, f"/{clean_p.rsplit('/', 1)[0]}")
        except Exception:
            pass

    return ApprovalRequestResponse(
        id=approval.id,
        tenant_id=approval.tenant_id,
        router_id=approval.router_id,
        router_name=router_name,
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

    from src.api.v1.vault import _verify_admin_totp

    checker_user = await db.get(User, checker_user_id) if type(db) is AsyncSession else None
    if isinstance(checker_user, User) and getattr(checker_user, "totp_enabled", False):
        if not payload.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código 2FA TOTP requerido para aprobar cambios críticos en la red",
            )
        await _verify_admin_totp(db, tenant_id, checker_user_id, payload.totp_code)
    elif payload.totp_code:
        await _verify_admin_totp(db, tenant_id, checker_user_id, payload.totp_code)

    if type(db) is AsyncSession:
        stmt_lock = (
            select(ApprovalRequest)
            .where(ApprovalRequest.id == approval_id, ApprovalRequest.tenant_id == tenant_id)
            .with_for_update()
        )
        approval = (await db.execute(stmt_lock)).scalar_one_or_none()
    else:
        approval = await db.get(ApprovalRequest, approval_id)
    if not approval or approval.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Solicitud de aprobación no encontrada")

    # Inquebrantable SoD: Quien solicita NUNCA puede dictaminar como Checker (salvo SUPERADMIN_GLOBAL)
    if approval.requested_by == checker_user_id and claims.get("rol") != SystemRoleEnum.SUPERADMIN_GLOBAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Violación Maker-Checker: El solicitante no puede dictaminar el rechazo formal como Checker",
        )

    if approval.status != ApprovalStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La solicitud no está pendiente (estado actual: {approval.status.value})",
        )

    now_utc = datetime.now(UTC)
    approval.status = ApprovalStatusEnum.REJECTED
    approval.reviewed_by = None if approval.requested_by == checker_user_id else checker_user_id
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
    await publish_maker_checker_event(
        tenant_id=tenant_id,
        event_name="MAKER_CHECKER_RESOLVED",
        approval_id=approval.id,
        summary=approval.summary,
        router_id=approval.router_id,
        resolution_status="REJECTED",
    )
    if approval.action_type == CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION:
        stmt_job = select(BulkJob).where(BulkJob.approval_request_id == approval.id)
        job_obj = (await db.execute(stmt_job)).scalar_one_or_none()
        if job_obj:
            job_obj.status = BulkJobStatusEnum.FAILED

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
