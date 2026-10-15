# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker 4: Rotación Automática Transaccional de Credenciales API de la Bóveda Criptográfica."""

import asyncio
import logging
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.webfig_common import _create_client_from_vault
from src.core.audit import write_audit_log
from src.core.crypto import encrypt_aes_gcm
from src.db.session import async_session_maker
from src.models.inventory import Router, RouterCredentialsVault

logger = logging.getLogger(__name__)

_SAFE_ROS_CHARACTERS = string.ascii_letters + string.digits + "!#$%&*+-.:;=?@^_~"


def _generate_safe_password() -> str:
    return "".join(secrets.choice(_SAFE_ROS_CHARACTERS) for _ in range(32))


async def _rotate_single_vault(
    session: Any,
    vault: RouterCredentialsVault,
    router_obj: Router,
) -> None:
    now_utc = datetime.now(UTC)
    new_password = _generate_safe_password()
    client = _create_client_from_vault(router_obj, router_obj.tenant_id)

    try:
        # 1. Modificar contraseña en el usuario de RouterOS
        await client.patch(f"user/{vault.api_username}", {"password": new_password})

        # 2. Respaldar actual como previa y cifrar nueva contraseña
        aad = f"{router_obj.tenant_id}:{router_obj.id}".encode()
        ct, iv, tag = encrypt_aes_gcm(new_password.encode("utf-8"), aad)

        vault.previous_password_ciphertext = vault.current_password_ciphertext
        vault.previous_password_iv = vault.current_password_iv
        vault.previous_password_tag = vault.current_password_tag

        vault.current_password_ciphertext = ct
        vault.current_password_iv = iv
        vault.current_password_tag = tag

        vault.last_rotated_at = now_utc
        interval = vault.rotation_interval_days or 30
        vault.next_rotation_due_at = now_utc + timedelta(days=interval)
        vault.last_rotation_status = "SUCCESS"

        await write_audit_log(
            session=session,
            tenant_id=router_obj.tenant_id,
            actor_username="system:vault_worker",
            actor_role="SUPERADMIN_GLOBAL",
            actor_ip="127.0.0.1",
            event_category="VAULT",
            event_action="VAULT_ROTATION_AUTOMATED",
            router_id=router_obj.id,
            router_display_name=router_obj.display_name,
            status_code=200,
        )
    except Exception as exc:
        logger.error("Fallo al rotar contraseña en MikroTik %s: %s", router_obj.display_name, exc)
        vault.last_rotation_status = f"FAILED: {exc}"
    finally:
        await client.close()


async def run_vault_rotation_cycle() -> None:
    """Busca credenciales que vencieron su intervalo de rotación y las renueva."""
    now_utc = datetime.now(UTC)
    async with async_session_maker() as session:
        stmt = (
            select(RouterCredentialsVault)
            .options(selectinload(RouterCredentialsVault.router))
            .where(
                RouterCredentialsVault.auto_rotate_enabled.is_(True),
                RouterCredentialsVault.next_rotation_due_at <= now_utc,
            )
        )
        vaults = (await session.execute(stmt)).scalars().all()
        for v in vaults:
            if v.router:
                await _rotate_single_vault(session, v, v.router)
        await session.commit()


async def vault_rotation_worker_loop() -> None:
    """Bucle del worker de rotación periódica de bóveda (cada 10 minutos)."""
    logger.info("Iniciando Worker 4: Rotación Automática Transaccional de Bóveda...")
    while True:
        try:
            await run_vault_rotation_cycle()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error en loop de rotación de bóveda: %s", exc)
        await asyncio.sleep(600.0)
