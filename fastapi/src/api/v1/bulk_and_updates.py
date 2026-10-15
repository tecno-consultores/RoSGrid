# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Gestión de Plantillas (Golden Configs), Acciones Masivas y Actualizador Centralizado de RouterOS v7."""

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.api.v1.webfig_common import get_router_and_client
from src.core.crypto import encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterTag
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    BulkJob,
    BulkJobItem,
    BulkJobStatusEnum,
    ConfigTemplate,
    CriticalActionTypeEnum,
    RouterBackup,
)
from src.schemas.bulk_and_updates import (
    BulkJobCreateRequest,
    BulkJobDetailResponse,
    BulkJobItemResponse,
    ConfigTemplateCreateRequest,
    ConfigTemplateResponse,
    RosFleetUpdateStatusResponse,
    RosUpdateExecuteRequest,
    RosUpdateExecuteResponse,
    RosUpdateRouterStatus,
    TemplateRenderPreviewRequest,
    TemplateRenderPreviewResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations", tags=["Bulk Operations & Updates"])

_OPERATOR_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
)

_ADMIN_OPERATIONS_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
)


def _render_template_steps(steps: list[dict[str, Any]], vars_dict: dict[str, Any]) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    raw_str = json.dumps(steps)
    for k, v in vars_dict.items():
        placeholder = f"{{{{ {k} }}}}"
        raw_str = raw_str.replace(placeholder, str(v))
        placeholder_no_space = f"{{{{{k}}}}}"
        raw_str = raw_str.replace(placeholder_no_space, str(v))
    rendered = json.loads(raw_str)
    return rendered


async def _resolve_target_router_ids(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    req: BulkJobCreateRequest,
) -> list[uuid.UUID]:
    if req.target_router_ids:
        return [uuid.UUID(r) for r in req.target_router_ids]
    if req.target_role:
        stmt = select(Router.id).where(
            Router.tenant_id == tenant_id,
            Router.network_role == req.target_role,
        )
        return list((await db.execute(stmt)).scalars().all())
    if req.target_tag:
        stmt = (
            select(RouterTag.router_id)
            .where(RouterTag.tenant_id == tenant_id, RouterTag.tag_name == req.target_tag)
            .distinct()
        )
        return list((await db.execute(stmt)).scalars().all())
    raise HTTPException(status_code=400, detail="Debe especificar target_router_ids, target_role o target_tag")


async def _perform_pre_upgrade_backup(
    client: MikrotikRestClient,
    router_obj: Router,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    try:
        raw_res = await client.post("export", {"terse": "false", "show-sensitive": "false"})
        raw_text = str(raw_res) if not isinstance(raw_res, str) else raw_res
        lines = [ln for ln in raw_text.splitlines() if not ln.strip().startswith("#")]
        cleaned = "\n".join(lines).strip()
        rsc_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

        aad = f"{tenant_id}:{router_obj.id}".encode()
        ct, iv, tag = encrypt_aes_gcm(cleaned.encode("utf-8"), aad)
        now_utc = datetime.now(UTC)

        backup = RouterBackup(
            tenant_id=tenant_id,
            router_id=router_obj.id,
            backup_type="PRE_UPGRADE",
            ros_version_at_backup=router_obj.ros_version or "7.16",
            rsc_sha256_hash=rsc_hash,
            rsc_size_bytes=len(cleaned.encode("utf-8")),
            rsc_ciphertext=ct,
            rsc_iv=iv,
            rsc_tag=tag,
            diff_lines_added=0,
            diff_lines_removed=0,
            triggered_by=user_id,
            created_at=now_utc,
            last_verified_identical_at=now_utc,
            expires_at=now_utc + timedelta(days=30),
        )
        db.add(backup)
        await db.flush()
        return True
    except Exception as exc:
        logger.error("Fallo de backup obligatorio previo al upgrade en %s: %s", router_obj.display_name, exc)
        return False


# ============================================================================
# PLANTILLAS (GOLDEN CONFIGS)
# ============================================================================


@router.get("/templates", response_model=list[ConfigTemplateResponse])
async def list_templates(
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[ConfigTemplateResponse]:
    """Lista plantillas de configuración del Tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(ConfigTemplate).where(ConfigTemplate.tenant_id == tenant_id).order_by(ConfigTemplate.name)
    templates = (await db.execute(stmt)).scalars().all()
    return [
        ConfigTemplateResponse(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            category=t.category,
            description=t.description,
            variables_schema=t.variables_schema,
            rest_steps_template=t.rest_steps_template,
            requires_safemode=t.requires_safemode,
            created_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]


@router.post("/templates", response_model=ConfigTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: ConfigTemplateCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ConfigTemplateResponse:
    """Crea una nueva plantilla parametrizable Golden Config."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])

    template = ConfigTemplate(
        tenant_id=tenant_id,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        variables_schema=payload.variables_schema,
        rest_steps_template=payload.rest_steps_template,
        requires_safemode=payload.requires_safemode,
        created_by=user_id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ConfigTemplateResponse(
        id=template.id,
        tenant_id=template.tenant_id,
        name=template.name,
        category=template.category,
        description=template.description,
        variables_schema=template.variables_schema,
        rest_steps_template=template.rest_steps_template,
        requires_safemode=template.requires_safemode,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/templates/{template_id}/render-preview", response_model=TemplateRenderPreviewResponse)
async def preview_template(
    template_id: uuid.UUID,
    payload: TemplateRenderPreviewRequest,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> TemplateRenderPreviewResponse:
    """Renderiza los pasos REST sustituyendo variables sin tocar ningún router."""
    tenant_id = uuid.UUID(claims["tid"])
    template = await db.get(ConfigTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    rendered = _render_template_steps(template.rest_steps_template, payload.variables)
    return TemplateRenderPreviewResponse(rendered_steps=rendered)


# ============================================================================
# TRABAJOS MASIVOS MULTI-ROUTER (BULK JOBS)
# ============================================================================


@router.post("/bulk-jobs", response_model=BulkJobDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_job(
    payload: BulkJobCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BulkJobDetailResponse:
    """Crea una acción masiva multi-router con intercepción Maker-Checker si el rol es SUPPORT_L2."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    role = claims.get("rol")

    target_ids = await _resolve_target_router_ids(db, tenant_id, payload)
    if not target_ids:
        raise HTTPException(status_code=400, detail="No se encontraron routers objetivo con los criterios dados")

    is_l2 = role == SystemRoleEnum.SUPPORT_L2.value
    job_status = BulkJobStatusEnum.AWAITING_APPROVAL if is_l2 else BulkJobStatusEnum.QUEUED

    approval_req_id: uuid.UUID | None = None
    if is_l2:
        now_utc = datetime.now(UTC)
        app_req = ApprovalRequest(
            tenant_id=tenant_id,
            action_type=CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION,
            status=ApprovalStatusEnum.PENDING,
            summary=f"Acción masiva: {payload.title} sobre {len(target_ids)} routers",
            requester_justification="Solicitud de ejecución masiva generada por Soporte N2",
            ros_rest_method="BULK",
            ros_rest_path="/operations/bulk-jobs",
            request_payload={"parameters": payload.execution_parameters},
            requested_by=user_id,
            expires_at=now_utc + timedelta(hours=24),
        )
        db.add(app_req)
        await db.flush()
        approval_req_id = app_req.id

    bulk_job = BulkJob(
        tenant_id=tenant_id,
        job_type=payload.job_type,
        title=payload.title,
        status=job_status,
        template_id=payload.template_id,
        execution_parameters=payload.execution_parameters,
        target_router_ids=[str(rid) for rid in target_ids],
        total_routers=len(target_ids),
        succeeded_count=0,
        failed_count=0,
        approval_request_id=approval_req_id,
        created_by=user_id,
    )
    db.add(bulk_job)
    await db.flush()

    for rid in target_ids:
        item = BulkJobItem(
            tenant_id=tenant_id,
            bulk_job_id=bulk_job.id,
            router_id=rid,
            status="PENDING",
        )
        db.add(item)

    await db.commit()
    await db.refresh(bulk_job)

    return await get_bulk_job(bulk_job.id, claims, db)


@router.get("/bulk-jobs/{job_id}", response_model=BulkJobDetailResponse)
async def get_bulk_job(
    job_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BulkJobDetailResponse:
    """Consulta el progreso en vivo de un trabajo masivo y el estado router por router."""
    tenant_id = uuid.UUID(claims["tid"])
    job = await db.get(BulkJob, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Trabajo masivo no encontrado")

    stmt = select(BulkJobItem).where(BulkJobItem.bulk_job_id == job_id)
    raw_items = (await db.execute(stmt)).scalars().all()

    items = [
        BulkJobItemResponse(
            id=i.id,
            router_id=i.router_id,
            status=i.status,
            response_summary=i.response_summary,
            error_detail=i.error_detail,
            started_at=i.started_at,
            finished_at=i.finished_at,
        )
        for i in raw_items
    ]

    return BulkJobDetailResponse(
        id=job.id,
        tenant_id=job.tenant_id,
        job_type=job.job_type,
        title=job.title,
        status=job.status.value,
        template_id=job.template_id,
        execution_parameters=job.execution_parameters,
        target_router_ids=job.target_router_ids,
        total_routers=job.total_routers,
        succeeded_count=job.succeeded_count,
        failed_count=job.failed_count,
        approval_request_id=job.approval_request_id,
        created_by=job.created_by,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        items=items,
    )


# ============================================================================
# ACTUALIZACIÓN CENTRALIZADA DE ROUTEROS v7 Y ROUTERBOOT
# ============================================================================


@router.get("/ros-updates/status", response_model=RosFleetUpdateStatusResponse)
async def get_fleet_updates_status(
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RosFleetUpdateStatusResponse:
    """Resumen de versiones de RouterOS y Firmware de toda la flota del Tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(Router).where(Router.tenant_id == tenant_id).order_by(Router.display_name)
    routers = (await db.execute(stmt)).scalars().all()

    statuses: list[RosUpdateRouterStatus] = []
    pending_count = 0
    up_to_date_count = 0

    for r in routers:
        has_update = False
        if (
            r.update_available_version
            and r.update_available_version != r.ros_version
            or r.upgrade_firmware_version
            and r.upgrade_firmware_version != r.firmware_version
        ):
            has_update = True

        if has_update:
            pending_count += 1
        else:
            up_to_date_count += 1

        statuses.append(
            RosUpdateRouterStatus(
                router_id=r.id,
                display_name=r.display_name,
                ros_version=r.ros_version,
                update_available_version=r.update_available_version,
                firmware_version=r.firmware_version,
                upgrade_firmware_version=r.upgrade_firmware_version,
                has_update=has_update,
            )
        )

    return RosFleetUpdateStatusResponse(
        total_routers=len(routers),
        up_to_date_count=up_to_date_count,
        pending_update_count=pending_count,
        routers=statuses,
    )


@router.post("/ros-updates/execute", response_model=RosUpdateExecuteResponse)
async def execute_fleet_updates(
    payload: RosUpdateExecuteRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RosUpdateExecuteResponse:
    """Lanza la actualización segura de RouterOS con backup previo obligatorio."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    results: list[dict[str, Any]] = []

    for rid in payload.router_ids:
        try:
            r_obj, client = await get_router_and_client(rid, claims, db)
            backup_ok = await _perform_pre_upgrade_backup(client, r_obj, tenant_id, user_id, db)
            if not backup_ok:
                results.append({"router_id": str(rid), "status": "ABORTED_PRE_BACKUP_FAILED"})
                continue

            if payload.auto_upgrade_firmware:
                await client.patch("system/routerboard/settings", {"auto-upgrade": "yes"})

            update_res = await client.post("system/package/update/install", {})
            results.append({"router_id": str(rid), "status": "UPGRADE_TRIGGERED", "detail": update_res})
        except Exception as exc:
            results.append({"router_id": str(rid), "status": "FAILED", "error": str(exc)})

    await db.commit()
    return RosUpdateExecuteResponse(
        status="COMPLETED",
        message=f"Procesadas {len(payload.router_ids)} solicitudes de actualización",
        results=results,
    )
