# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Endpoints CRUD para Canales de Notificación y Pruebas de Despacho de Alertas."""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, cast

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
from src.workers.alert_dispatcher_worker import (
    _dispatch_smtp_sync,
    _dispatch_telegram,
    _dispatch_webhook,
    _resolve_smtp_recipients,
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
    aad = f"{tenant_id}:{channel_id}".encode()
    raw_json = json.dumps(config).encode("utf-8")
    return encrypt_aes_gcm(raw_json, aad)


def _decrypt_channel_config(tenant_id: uuid.UUID, ch: NotificationChannel) -> dict[str, Any]:
    aad = f"{tenant_id}:{ch.id}".encode()
    decrypted = decrypt_aes_gcm(ch.config_ciphertext, ch.config_iv, ch.config_tag, aad)
    return cast(dict[str, Any], json.loads(decrypted.decode("utf-8")))


def _build_safe_config_summary(tenant_id: uuid.UUID, ch: NotificationChannel) -> dict[str, Any]:
    try:
        conf = _decrypt_channel_config(tenant_id, ch)
    except Exception:
        return {}

    ch_type = ch.channel_type.value if hasattr(ch.channel_type, "value") else str(ch.channel_type)
    if ch_type == "TELEGRAM_BOT":
        return {
            "chat_id": conf.get("chat_id", ""),
            "has_bot_token": bool(conf.get("bot_token")),
        }
    if ch_type == "SMTP_EMAIL":
        raw_to = conf.get("to_emails") or conf.get("to_addresses") or []
        if isinstance(raw_to, str):
            to_list = [s.strip() for s in raw_to.split(",") if s.strip()]
        elif isinstance(raw_to, list):
            to_list = [str(s).strip() for s in raw_to if str(s).strip()]
        else:
            to_list = []
        return {
            "smtp_host": conf.get("smtp_host", ""),
            "smtp_port": int(conf.get("smtp_port", 587)),
            "smtp_user": conf.get("smtp_user", ""),
            "from_email": conf.get("from_email", ""),
            "to_emails": to_list,
            "has_password": bool(conf.get("smtp_password")),
        }
    if ch_type == "GENERIC_WEBHOOK":
        return {
            "webhook_url": conf.get("webhook_url", ""),
            "has_auth_header": bool(conf.get("auth_header") or conf.get("secret")),
        }
    return {}


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
        select(NotificationChannel).where(NotificationChannel.tenant_id == tenant_id).order_by(NotificationChannel.name)
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
            config_summary=_build_safe_config_summary(tenant_id, r),
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
        config_summary=_build_safe_config_summary(tenant_id, channel),
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
        try:
            existing_conf = _decrypt_channel_config(tenant_id, channel)
        except Exception:
            existing_conf = {}

        new_conf = dict(payload.config)
        # Preservar secretos existentes si en payload vienen vacíos o None
        if not new_conf.get("smtp_password") and existing_conf.get("smtp_password"):
            new_conf["smtp_password"] = existing_conf["smtp_password"]
        if not new_conf.get("bot_token") and existing_conf.get("bot_token"):
            new_conf["bot_token"] = existing_conf["bot_token"]
        if not new_conf.get("auth_header") and existing_conf.get("auth_header"):
            new_conf["auth_header"] = existing_conf["auth_header"]
        if not new_conf.get("secret") and existing_conf.get("secret"):
            new_conf["secret"] = existing_conf["secret"]

        merged_conf = {**existing_conf, **new_conf}
        ct, iv, tag = _encrypt_channel_config(tenant_id, channel.id, merged_conf)
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
        config_summary=_build_safe_config_summary(tenant_id, channel),
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
    ch_type = channel.channel_type.value if hasattr(channel.channel_type, "value") else str(channel.channel_type)

    # Verificación de sintaxis y Anti-SSRF de configuración según canal
    if ch_type == "TELEGRAM_BOT" and ("bot_token" not in conf or "chat_id" not in conf):
        return NotificationTestResponse(status="FAILED", detail="Faltan 'bot_token' o 'chat_id'")
    if ch_type == "GENERIC_WEBHOOK":
        if "webhook_url" not in conf or not str(conf.get("webhook_url", "")).strip():
            return NotificationTestResponse(status="FAILED", detail="Falta 'webhook_url'")
        from src.core.ssrf import is_safe_outbound_url_async

        if not await is_safe_outbound_url_async(str(conf["webhook_url"]), allow_private_cidrs=[]):
            return NotificationTestResponse(
                status="FAILED",
                detail="Fallo al enviar prueba (GENERIC_WEBHOOK): URL bloqueada por política Anti-SSRF",
            )
    if ch_type == "SMTP_EMAIL":
        if "smtp_host" not in conf or not str(conf.get("smtp_host", "")).strip():
            return NotificationTestResponse(status="FAILED", detail="Falta 'smtp_host'")
        from src.core.ssrf import is_safe_smtp_target

        smtp_host_val = str(conf.get("smtp_host", "")).strip()
        smtp_port_val = int(conf.get("smtp_port") or 587)
        if not is_safe_smtp_target(smtp_host_val, smtp_port_val, allow_localhost_fallback=False):
            return NotificationTestResponse(
                status="FAILED",
                detail="Fallo al enviar prueba (SMTP_EMAIL): Servidor o puerto SMTP bloqueado por política Anti-SSRF",
            )
        recipients = _resolve_smtp_recipients(conf)
        if not recipients:
            return NotificationTestResponse(
                status="FAILED", detail="Falta indicar al menos un destinatario ('to_emails')"
            )

    alert_payload = {
        "event_name": "CHANNEL_TEST",
        "channel_name": channel.name,
        "router_display_name": "RoSGrid Control Plane",
        "operational_status": "ONLINE",
        "timestamp_iso": datetime.now(UTC).isoformat(),
        "custom_message": payload.message or f"Prueba de alerta desde el canal {channel.name}",
    }

    try:
        if ch_type == "SMTP_EMAIL":
            await asyncio.to_thread(_dispatch_smtp_sync, conf, alert_payload)
            to_repr = ", ".join(_resolve_smtp_recipients(conf))
            detail_msg = f"Correo de prueba enviado con éxito a {to_repr} vía {conf.get('smtp_host')}:{conf.get('smtp_port', 587)}"
        elif ch_type == "TELEGRAM_BOT":
            await _dispatch_telegram(conf, alert_payload)
            detail_msg = f"Mensaje de prueba enviado con éxito a Telegram (chat {conf.get('chat_id')})"
        elif ch_type == "GENERIC_WEBHOOK":
            dispatched = await _dispatch_webhook(conf, alert_payload)
            if dispatched is False:
                return NotificationTestResponse(
                    status="FAILED",
                    detail="Fallo al enviar prueba (GENERIC_WEBHOOK): URL bloqueada por política Anti-SSRF",
                )
            detail_msg = f"Webhook de prueba despachado con éxito a {conf.get('webhook_url')}"
        else:
            detail_msg = f"Configuración de canal {ch_type} validada con éxito"

        return NotificationTestResponse(status="SUCCESS", detail=detail_msg)
    except Exception as exc:
        logger.warning("Fallo al enviar prueba en canal %s (%s): %s", channel.name, ch_type, exc)
        return NotificationTestResponse(
            status="FAILED",
            detail=f"Fallo al enviar prueba ({ch_type}): {exc}",
        )
