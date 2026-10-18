# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Motor de Respaldos RouterOS v7 (.rsc/.backup), Deduplicación SHA-256 y Comparador Diff estilo Git."""

import asyncio
import difflib
import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.api.v1.webfig_common import get_router_and_client
from src.core.audit import write_audit_log
from src.core.crypto import decrypt_aes_gcm, encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.models.operations import RouterBackup
from src.schemas.backups import (
    BackupDiffHunk,
    BackupGitDiffResponse,
    BackupItemResponse,
    BackupListResponse,
    BackupTriggerResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/backups", tags=["Backups & Diff"])

_ALLOWED_BACKUP_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.INVENTORY_MANAGER,
    SystemRoleEnum.AUDITOR,
)

_TRIGGER_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
    SystemRoleEnum.INVENTORY_MANAGER,
)


def clean_rsc_export_comments(raw_text: str) -> str:
    """Elimina comentarios de cabecera con timestamps volátiles de RouterOS."""
    lines = [line for line in raw_text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(lines).strip()


def _extract_raw_rsc_text(export_res: Any) -> str:
    if isinstance(export_res, str):
        return export_res
    if isinstance(export_res, list):
        return "\n".join(str(item) for item in export_res)
    if isinstance(export_res, dict):
        return str(export_res.get("ret", export_res.get("detail", str(export_res))))
    return str(export_res)


async def export_router_rsc(client: MikrotikRestClient) -> str:
    """Exporta configuración completa del router leyendo el archivo temporal .rsc y limpiándolo."""
    fname = f"rosgrid_bk_{uuid.uuid4().hex[:8]}"
    raw_text = ""
    try:
        await client.post("export", json_data={"file": fname, "show-sensitive": "false"})
        await asyncio.sleep(1.0)
        files = await client.get("file")
        if isinstance(files, list):
            target_files = [f for f in files if f.get("name") in (f"{fname}.rsc", fname)]
            if target_files:
                tf = target_files[0]
                raw_text = tf.get("contents", "")
                file_id = tf.get(".id")
                if file_id:
                    try:
                        await client.delete(f"file/{file_id}")
                    except Exception as del_err:
                        logger.debug("Error eliminando archivo temporal en router: %s", del_err)
    except Exception as exc:
        logger.warning("Fallo al exportar via archivo en router: %s", exc)

    if not raw_text:
        raw_res = await client.post("export", json_data={"terse": "false", "show-sensitive": "false"})
        raw_text = _extract_raw_rsc_text(raw_res)

    cleaned = clean_rsc_export_comments(raw_text)
    if not cleaned:
        raise HTTPException(
            status_code=502,
            detail="El router no devolvió configuración o no tiene permisos de exportación (requiere política 'ftp' en MikroTik).",
        )
    return cleaned


def _compute_diff_stats(base_lines: list[str], target_lines: list[str]) -> tuple[int, int, list[str]]:
    diff_gen = list(
        difflib.unified_diff(
            base_lines,
            target_lines,
            fromfile="base.rsc",
            tofile="target.rsc",
            lineterm="",
        )
    )
    added = sum(1 for line in diff_gen if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_gen if line.startswith("-") and not line.startswith("---"))
    return added, removed, diff_gen


def _build_side_by_side_hunks(diff_lines: list[str]) -> list[BackupDiffHunk]:
    hunks: list[BackupDiffHunk] = []
    current_sec = ""
    for line in diff_lines:
        if line.startswith("@@") or line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("/"):
            current_sec = line.strip()
        elif line.startswith("+"):
            hunks.append(BackupDiffHunk(section_header=current_sec, change_type="ADDED", new_text=line[1:].strip()))
        elif line.startswith("-"):
            hunks.append(BackupDiffHunk(section_header=current_sec, change_type="REMOVED", old_text=line[1:].strip()))
    return hunks


def _decrypt_backup_rsc(backup: RouterBackup, tenant_id: uuid.UUID) -> str:
    aad = f"{tenant_id}:{backup.router_id}".encode()
    decrypted_bytes = decrypt_aes_gcm(backup.rsc_ciphertext, backup.rsc_iv, backup.rsc_tag, aad)
    return decrypted_bytes.decode("utf-8")


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=BackupListResponse)
async def list_backups(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_ALLOWED_BACKUP_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BackupListResponse:
    """Historial de respaldos del router con ventana de retención de 30 días."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = (
        select(RouterBackup)
        .where(RouterBackup.tenant_id == tenant_id, RouterBackup.router_id == router_id)
        .order_by(desc(RouterBackup.created_at))
    )
    records = (await db.execute(stmt)).scalars().all()

    items = [
        BackupItemResponse(
            id=r.id,
            backup_type=r.backup_type,
            ros_version_at_backup=r.ros_version_at_backup,
            rsc_sha256_hash=r.rsc_sha256_hash,
            rsc_size_bytes=r.rsc_size_bytes,
            diff_lines_added=r.diff_lines_added,
            diff_lines_removed=r.diff_lines_removed,
            parent_backup_id=r.parent_backup_id,
            has_binary_backup=r.binary_backup_file_path is not None,
            created_at=r.created_at,
            last_verified_identical_at=r.last_verified_identical_at,
            expires_at=r.expires_at,
        )
        for r in records
    ]
    return BackupListResponse(router_id=router_id, retention_days=30, items=items)


@router.post("/trigger", response_model=BackupTriggerResponse)
async def trigger_backup(
    router_id: uuid.UUID,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_TRIGGER_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BackupTriggerResponse:
    """Dispara un respaldo manual inmediato (.rsc) con deduplicación por SHA-256."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    router_obj, client = await get_router_and_client(router_id, claims, db)

    cleaned_rsc = await export_router_rsc(client)

    rsc_hash = hashlib.sha256(cleaned_rsc.encode("utf-8")).hexdigest()
    now_utc = datetime.now(UTC)

    latest_stmt = (
        select(RouterBackup)
        .where(RouterBackup.tenant_id == tenant_id, RouterBackup.router_id == router_id)
        .order_by(desc(RouterBackup.created_at))
        .limit(1)
    )
    latest_backup = (await db.execute(latest_stmt)).scalar_one_or_none()

    if latest_backup and latest_backup.rsc_sha256_hash == rsc_hash:
        latest_backup.last_verified_identical_at = now_utc
        await db.commit()
        return BackupTriggerResponse(
            status="IDENTICAL_SKIPPED_DEDUPLICATED",
            backup_id=latest_backup.id,
            rsc_sha256_hash=rsc_hash,
            message="Configuración idéntica al último respaldo. Se deduplica sin generar almacenamiento redundante.",
        )

    lines_added, lines_removed = 0, 0
    if latest_backup:
        old_text = clean_rsc_export_comments(_decrypt_backup_rsc(latest_backup, tenant_id))
        lines_added, lines_removed, _ = _compute_diff_stats(old_text.splitlines(), cleaned_rsc.splitlines())

    aad = f"{tenant_id}:{router_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(cleaned_rsc.encode("utf-8"), aad)

    new_backup = RouterBackup(
        tenant_id=tenant_id,
        router_id=router_id,
        backup_type="MANUAL_OPERATOR",
        ros_version_at_backup=router_obj.ros_version or "7.16",
        rsc_sha256_hash=rsc_hash,
        rsc_size_bytes=len(cleaned_rsc.encode("utf-8")),
        rsc_ciphertext=ct,
        rsc_iv=iv,
        rsc_tag=tag,
        diff_lines_added=lines_added,
        diff_lines_removed=lines_removed,
        parent_backup_id=latest_backup.id if latest_backup else None,
        triggered_by=user_id,
        created_at=now_utc,
        last_verified_identical_at=now_utc,
        expires_at=now_utc + timedelta(days=30),
    )
    db.add(new_backup)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "operator"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="BACKUPS",
        event_action="ROUTER_BACKUP_CREATED",
        actor_user_id=user_id,
        router_id=router_id,
        router_display_name=router_obj.display_name,
        after_state={"rsc_sha256_hash": rsc_hash, "lines_added": lines_added, "lines_removed": lines_removed},
        status_code=201,
    )
    await db.commit()
    await db.refresh(new_backup)

    return BackupTriggerResponse(
        status="CREATED",
        backup_id=new_backup.id,
        rsc_sha256_hash=rsc_hash,
        message="Respaldo cifrado generado y guardado exitosamente.",
    )


@router.get("/diff", response_model=BackupGitDiffResponse)
async def get_backup_diff(
    router_id: uuid.UUID,
    base_backup_id: uuid.UUID = Query(...),
    target_backup_id: str = Query(...),
    claims: dict[str, Any] = Depends(require_roles(*_ALLOWED_BACKUP_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BackupGitDiffResponse:
    """Comparador visual de configuraciones estilo Git (unified_diff) entre dos respaldos o contra LIVE."""
    tenant_id = uuid.UUID(claims["tid"])
    base_backup = await db.get(RouterBackup, base_backup_id)
    if not base_backup or base_backup.tenant_id != tenant_id or base_backup.router_id != router_id:
        raise HTTPException(status_code=404, detail="Respaldo base no encontrado")

    base_rsc = clean_rsc_export_comments(_decrypt_backup_rsc(base_backup, tenant_id))

    if target_backup_id.upper() == "LIVE":
        _, client = await get_router_and_client(router_id, claims, db)
        live_res = await client.post("export", {"terse": "false", "show-sensitive": "false"})
        target_rsc = clean_rsc_export_comments(_extract_raw_rsc_text(live_res))
        target_created_at = datetime.now(UTC).isoformat()
    else:
        try:
            target_uuid = uuid.UUID(target_backup_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="target_backup_id debe ser un UUID o 'LIVE'") from exc
        target_backup = await db.get(RouterBackup, target_uuid)
        if not target_backup or target_backup.tenant_id != tenant_id or target_backup.router_id != router_id:
            raise HTTPException(status_code=404, detail="Respaldo objetivo no encontrado")
        target_rsc = clean_rsc_export_comments(_decrypt_backup_rsc(target_backup, tenant_id))
        target_created_at = target_backup.created_at.isoformat()

    added, removed, diff_lines = _compute_diff_stats(base_rsc.splitlines(), target_rsc.splitlines())
    hunks = _build_side_by_side_hunks(diff_lines)

    return BackupGitDiffResponse(
        router_id=router_id,
        base_backup_id=str(base_backup.id),
        base_created_at=base_backup.created_at.isoformat(),
        target_backup_id=target_backup_id,
        target_created_at=target_created_at,
        lines_added=added,
        lines_removed=removed,
        unified_diff_text="\n".join(diff_lines),
        side_by_side_hunks=hunks,
        base_content=base_rsc,
        target_content=target_rsc,
    )


@router.get("/{backup_id}/download")
async def download_backup_file(
    router_id: uuid.UUID,
    backup_id: uuid.UUID,
    format: str = Query("rsc", pattern="^(rsc|backup)$"),
    claims: dict[str, Any] = Depends(require_roles(*_ALLOWED_BACKUP_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Response:
    """Descarga el respaldo .rsc descifrado en texto plano."""
    tenant_id = uuid.UUID(claims["tid"])
    backup = await db.get(RouterBackup, backup_id)
    if not backup or backup.tenant_id != tenant_id or backup.router_id != router_id:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")

    rsc_text = clean_rsc_export_comments(_decrypt_backup_rsc(backup, tenant_id))
    fname = f"rosgrid-backup-{router_id}-{str(backup.id)[:8]}.{format}"
    return Response(
        content=rsc_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
