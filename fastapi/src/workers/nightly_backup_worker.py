# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker 3: Respaldos Nocturnos Automatizados con Deduplicación SHA-256 y Purga de Retención (30 Días)."""

import asyncio
import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from src.api.v1.backups import clean_rsc_export_comments, export_router_rsc
from src.api.v1.webfig_common import _create_client_from_vault
from src.core.crypto import encrypt_aes_gcm
from src.db.session import async_session_maker
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.operations import RouterBackup

logger = logging.getLogger(__name__)


async def _purge_expired_backups(session: Any) -> int:
    now_utc = datetime.now(UTC)
    stmt = (
        select(RouterBackup)
        .where(RouterBackup.expires_at < now_utc)
        .order_by(RouterBackup.router_id, desc(RouterBackup.created_at))
    )
    expired = (await session.execute(stmt)).scalars().all()
    purged = 0
    seen_routers: set[uuid.UUID] = set()

    for b in expired:
        # Garantía inquebrantable: Conservar siempre al menos el último respaldo de cada equipo
        if b.router_id not in seen_routers:
            latest_stmt = (
                select(RouterBackup.id)
                .where(RouterBackup.router_id == b.router_id)
                .order_by(desc(RouterBackup.created_at))
                .limit(1)
            )
            latest_id = (await session.execute(latest_stmt)).scalar_one_or_none()
            if latest_id == b.id:
                seen_routers.add(b.router_id)
                continue

        await session.delete(b)
        purged += 1

    return purged


async def _backup_single_router(session: Any, r: Router) -> None:
    if not r.vault:
        return
    client = _create_client_from_vault(r, r.tenant_id)
    try:
        cleaned_rsc = await export_router_rsc(client)
        rsc_hash = hashlib.sha256(cleaned_rsc.encode("utf-8")).hexdigest()
        now_utc = datetime.now(UTC)

        latest_stmt = (
            select(RouterBackup)
            .where(RouterBackup.tenant_id == r.tenant_id, RouterBackup.router_id == r.id)
            .order_by(desc(RouterBackup.created_at))
            .limit(1)
        )
        latest = (await session.execute(latest_stmt)).scalar_one_or_none()

        if latest and latest.rsc_sha256_hash == rsc_hash:
            latest.last_verified_identical_at = now_utc
            return

        aad = f"{r.tenant_id}:{r.id}".encode()
        ct, iv, tag = encrypt_aes_gcm(cleaned_rsc.encode("utf-8"), aad)

        backup = RouterBackup(
            tenant_id=r.tenant_id,
            router_id=r.id,
            backup_type="AUTOMATIC_NIGHTLY",
            ros_version_at_backup=r.ros_version or "7.16",
            rsc_sha256_hash=rsc_hash,
            rsc_size_bytes=len(cleaned_rsc.encode("utf-8")),
            rsc_ciphertext=ct,
            rsc_iv=iv,
            rsc_tag=tag,
            parent_backup_id=latest.id if latest else None,
            created_at=now_utc,
            last_verified_identical_at=now_utc,
            expires_at=now_utc + timedelta(days=30),
        )
        session.add(backup)
    finally:
        await client.close()


async def run_nightly_backup_cycle() -> None:
    """Ejecuta el ciclo de respaldo nocturno para la flota completa y purga respaldos > 30 días."""
    logger.info("Iniciando ronda de respaldos nocturnos deduplicados...")
    async with async_session_maker() as session:
        stmt = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.admin_state == RouterAdminStateEnum.PRODUCTION)
        )
        routers = (await session.execute(stmt)).scalars().all()
        for r in routers:
            try:
                await _backup_single_router(session, r)
            except Exception as exc:
                logger.error("Error en respaldo nocturno de %s: %s", r.display_name, exc)

        purged_count = await _purge_expired_backups(session)
        await session.commit()
        logger.info("Ronda de respaldos completada. Respaldos purgados (> 30 días): %d", purged_count)


async def nightly_backup_worker_loop() -> None:
    """Bucle del worker nocturno (se ejecuta cada 24 horas tras un ciclo inicial)."""
    logger.info("Iniciando Worker 3: Respaldos Nocturnos y Retención...")
    while True:
        try:
            await run_nightly_backup_cycle()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error en loop de respaldos nocturnos: %s", exc)
        await asyncio.sleep(86400.0)
