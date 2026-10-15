# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Bóveda Criptográfica: Revelación con Step-Up Auth (30s) y Rotación Transaccional."""

import logging
import secrets
import string
import uuid
from datetime import UTC, datetime
from typing import Any

import pyotp
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import write_audit_log
from src.core.crypto import decrypt_aes_gcm, encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum, User
from src.models.inventory import Router, RouterCredentialsVault
from src.schemas.inventory import (
    VaultRevealRequest,
    VaultRevealResponse,
    VaultRotateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory/routers", tags=["Vault"])

_SAFE_ROS_CHARACTERS = string.ascii_letters + string.digits + "!#$%&*+-.:;=?@^_~"


async def _verify_admin_totp(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, totp_code: str) -> User:
    user = await db.get(User, user_id)
    if not user or not user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene configurado 2FA TOTP para Step-Up Auth",
        )
    aad = f"{tenant_id}:{user.id}".encode("utf-8")
    secret = decrypt_aes_gcm(
        user.totp_secret_ciphertext,
        user.totp_secret_iv,
        user.totp_secret_tag,
        aad,
    ).decode("utf-8")
    if not pyotp.TOTP(secret).verify(totp_code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código 2FA TOTP inválido o expirado",
        )
    return user


def _generate_safe_ros_password(length: int = 32) -> str:
    """Genera una contraseña criptográfica segura compatible con CLI y REST API de RouterOS."""
    return "".join(secrets.choice(_SAFE_ROS_CHARACTERS) for _ in range(length))


def _decrypt_vault_passwords(
    vault: RouterCredentialsVault,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
) -> tuple[str, str | None]:
    aad = f"{tenant_id}:{router_id}".encode("utf-8")
    cur_pass = decrypt_aes_gcm(
        vault.current_password_ciphertext,
        vault.current_password_iv,
        vault.current_password_tag,
        aad,
    ).decode("utf-8")

    prev_pass: str | None = None
    if vault.previous_password_ciphertext and vault.previous_password_iv and vault.previous_password_tag:
        prev_pass = decrypt_aes_gcm(
            vault.previous_password_ciphertext,
            vault.previous_password_iv,
            vault.previous_password_tag,
            aad,
        ).decode("utf-8")
    return cur_pass, prev_pass


@router.post("/{router_id}/vault/reveal", response_model=VaultRevealResponse)
async def reveal_credentials(
    router_id: uuid.UUID,
    payload: VaultRevealRequest,
    request: Request,
    response: Response,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> VaultRevealResponse:
    """Revela credenciales con Step-Up Auth de 30 segundos (Exclusivo Superadmin y Tenant Admin)."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    admin_user = await _verify_admin_totp(db, tenant_id, user_id, payload.totp_code)

    query = select(Router).options(selectinload(Router.vault)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(query)).scalar_one_or_none()
    if not r or not r.vault:
        raise HTTPException(status_code=404, detail="Router o registro en bóveda no encontrado")

    cur_pass, prev_pass = _decrypt_vault_passwords(r.vault, tenant_id, r.id)

    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent")
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=admin_user.id,
        actor_username=admin_user.username,
        actor_role=admin_user.role,
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="SECURITY",
        event_action="CREDENTIAL_REVEALED",
        router_id=r.id,
        router_display_name=r.display_name,
        before_state={"reason": payload.reason},
    )
    await db.commit()

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"

    return VaultRevealResponse(
        router_id=r.id,
        api_username=r.vault.api_username,
        current_password=cur_pass,
        previous_password=prev_pass,
        last_rotated_at=r.vault.last_rotated_at,
        next_rotation_due_at=r.vault.next_rotation_due_at,
        display_ttl_seconds=30,
    )


async def _rotate_on_device(
    r: Router,
    vault: RouterCredentialsVault,
    old_pass: str,
    new_pass: str,
) -> None:
    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    async with MikrotikRestClient(
        host=host,
        port=r.api_port,
        username=vault.api_username,
        password=old_pass,
        ssl_pinned_fingerprint=r.ssl_sha256_fingerprint,
        timeout=10.0,
    ) as client:
        await client.patch(f"/user/{vault.api_username}", json_data={"password": new_pass})

    async with MikrotikRestClient(
        host=host,
        port=r.api_port,
        username=vault.api_username,
        password=new_pass,
        ssl_pinned_fingerprint=r.ssl_sha256_fingerprint,
        timeout=10.0,
    ) as verify_client:
        res = await verify_client.get("/system/identity")
        if not res:
            raise HTTPException(status_code=502, detail="Fallo de verificación de nueva contraseña en MikroTik")


@router.post("/{router_id}/vault/rotate-now", response_model=VaultRotateResponse)
async def rotate_now(
    router_id: uuid.UUID,
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
) -> VaultRotateResponse:
    """Rotación transaccional inmediata de la contraseña de la API REST en el router MikroTik."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])

    query = select(Router).options(selectinload(Router.vault)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(query)).scalar_one_or_none()
    if not r or not r.vault:
        raise HTTPException(status_code=404, detail="Router o credenciales no encontradas")

    cur_pass, _ = _decrypt_vault_passwords(r.vault, tenant_id, r.id)
    new_pass = _generate_safe_ros_password(32)

    await _rotate_on_device(r, r.vault, cur_pass, new_pass)

    aad = f"{tenant_id}:{r.id}".encode("utf-8")
    new_ct, new_iv, new_tag = encrypt_aes_gcm(new_pass.encode("utf-8"), aad)

    r.vault.previous_password_ciphertext = r.vault.current_password_ciphertext
    r.vault.previous_password_iv = r.vault.current_password_iv
    r.vault.previous_password_tag = r.vault.current_password_tag

    r.vault.current_password_ciphertext = new_ct
    r.vault.current_password_iv = new_iv
    r.vault.current_password_tag = new_tag
    r.vault.last_rotated_at = datetime.now(UTC)
    r.vault.last_rotation_status = "SUCCESS"
    r.vault.updated_by = user_id

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
        event_category="SECURITY",
        event_action="CREDENTIAL_AUTO_ROTATED",
        router_id=r.id,
        router_display_name=r.display_name,
    )
    await db.commit()

    return VaultRotateResponse(
        router_id=r.id,
        status="SUCCESS",
        last_rotated_at=r.vault.last_rotated_at,
    )
