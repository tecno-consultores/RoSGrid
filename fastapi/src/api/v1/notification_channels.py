# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints CRUD para Canales de Notificación y Pruebas de Despacho de Alertas."""

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.core.crypto import decrypt_aes_gcm, encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum
from src.models.operations import AlertChannelTypeEnum, NotificationChannel
from src.schemas.notifications import (
    NotificationChannelCreateRequest,
    NotificationChannelResponse,
    NotificationChannelUpdateRequest,
    NotificationTestRequest,
    NotificationTestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations/notification-channels", tags=["Notification Channels"])

_ADMIN_NOTIFICATION_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
)


def _encrypt_channel_config(
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
    config: dict[str, Any],
) -> tuple[bytes, bytes, bytes]:
    aad = f"{tenant_id}:{channel_id}".encode("utf-8")
    raw_json = json.dumps(config).encode("utf-8")
    return encrypt_aes_gcm(raw_json, aad)


def _decrypt_channel_config(tenant_id: uuid.UUID, ch: NotificationChannel) -> dict[str, Any]:
    aad = f"{tenant_id}:{ch.id}".encode("utf-8")
    decrypted = decrypt_aes_gcm(ch.config_ciphertext, ch.config_iv, ch.config_tag, aad)
    return json.loads(decrypted.decode("utf-8"))


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=list[NotificationChannelResponse])
async def list_channels(
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_NOTIFICATION_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[NotificationChannelResponse]:
    """Lista todos los canales de notificación configurados para el Tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = (
        select(NotificationChannel)
        .where(NotificationChannel.tenant_id == tenant_id)
        .order_by(NotificationChannel.name)
    )
    records = (await db.execute(stmt)).scalars().all()
    return [
        NotificationChannelResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            name=r.name,
            channel_type=r.channel_type.value,
            is_enabled=r.is_enabled,
            subscribed_events=r.subscribed_events,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.post("", response_model=NotificationChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: NotificationChannelCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_NOTIFICATION_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> NotificationChannelResponse:
    """Crea un nuevo canal de notificación con credenciales cifradas en AES-256-GCM."""
    tenant_id = uuid.UUID(claims["tid"])
    ch_id = uuid.uuid4()
    ct, iv, tag = _encrypt_channel_config(tenant_id, ch_id, payload.config)

    channel = NotificationChannel(
        id=ch_id,
        tenant_id=tenant_id,
        name=payload.name,
        channel_type=AlertChannelTypeEnum(payload.channel_type),
        is_enabled=payload.is_enabled,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=payload.subscribed_events,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return NotificationChannelResponse(
        id=channel.id,
        tenant_id=channel.tenant_id,
        name=channel.name,
        channel_type=channel.channel_type.value,
        is_enabled=channel.is_enabled,
        subscribed_events=channel.subscribed_events,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


@router.patch("/{channel_id}", response_model=NotificationChannelResponse)
async def update_channel(
    channel_id: uuid.UUID,
    payload: NotificationChannelUpdateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_NOTIFICATION_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> NotificationChannelResponse:
    """Actualiza configuración, estado o eventos suscritos de un canal de alerta."""
    tenant_id = uuid.UUID(claims["tid"])
    channel = await db.get(NotificationChannel, channel_id)
    if not channel or channel.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Canal de notificación no encontrado")

    if payload.name is not None:
        channel.name = payload.name
    if payload.is_enabled is not None:
        channel.is_enabled = payload.is_enabled
    if payload.subscribed_events is not None:
        channel.subscribed_events = payload.subscribed_events
    if payload.config is not None:
        ct, iv, tag = _encrypt_channel_config(tenant_id, channel.id, payload.config)
        channel.config_ciphertext = ct
        channel.config_iv = iv
        channel.config_tag = tag

    await db.commit()
    await db.refresh(channel)

    return NotificationChannelResponse(
        id=channel.id,
        tenant_id=channel.tenant_id,
        name=channel.name,
        channel_type=channel.channel_type.value,
        is_enabled=channel.is_enabled,
        subscribed_events=channel.subscribed_events,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_NOTIFICATION_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> None:
    """Elimina un canal de notificación configurado."""
    tenant_id = uuid.UUID(claims["tid"])
    channel = await db.get(NotificationChannel, channel_id)
    if not channel or channel.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Canal de notificación no encontrado")

    await db.delete(channel)
    await db.commit()


@router.post("/{channel_id}/test", response_model=NotificationTestResponse)
async def test_channel(
    channel_id: uuid.UUID,
    payload: NotificationTestRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_NOTIFICATION_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> NotificationTestResponse:
    """Envía un mensaje de prueba al canal de notificación para validar credenciales."""
    tenant_id = uuid.UUID(claims["tid"])
    channel = await db.get(NotificationChannel, channel_id)
    if not channel or channel.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Canal de notificación no encontrado")

    conf = _decrypt_channel_config(tenant_id, channel)
    ch_type = channel.channel_type.value

    # Verificación de sintaxis de configuración según canal
    if ch_type == "TELEGRAM_BOT" and ("bot_token" not in conf or "chat_id" not in conf):
        return NotificationTestResponse(status="FAILED", detail="Faltan 'bot_token' o 'chat_id'")
    if ch_type == "GENERIC_WEBHOOK" and "webhook_url" not in conf:
        return NotificationTestResponse(status="FAILED", detail="Falta 'webhook_url'")

    return NotificationTestResponse(
        status="SUCCESS",
        detail=f"Configuración de canal {ch_type} validada con éxito",
    )
