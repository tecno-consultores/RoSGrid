# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker 2: Despachador Multi-Canal de Alertas (Telegram, SMTP, Webhook firmado y Wallboard NOC)."""

import asyncio
import hashlib
import hmac
import json
import logging
import smtplib
import uuid
from email.message import EmailMessage
from typing import Any

import httpx
from sqlalchemy import select

from src.core.crypto import decrypt_aes_gcm
from src.db.session import async_session_maker
from src.models.operations import AlertChannelTypeEnum, NotificationChannel
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)


def _decrypt_config(tenant_id: uuid.UUID, ch: NotificationChannel) -> dict[str, Any]:
    aad = f"{tenant_id}:{ch.id}".encode("utf-8")
    raw = decrypt_aes_gcm(ch.config_ciphertext, ch.config_iv, ch.config_tag, aad)
    return json.loads(raw.decode("utf-8"))


async def _dispatch_telegram(config: dict[str, Any], alert: dict[str, Any]) -> None:
    bot_token = config.get("bot_token")
    chat_id = config.get("chat_id")
    if not bot_token or not chat_id:
        return

    text = (
        f"🚨 *Alerta RoSGrid*\n"
        f"• *Evento:* `{alert.get('event_name')}`\n"
        f"• *Router:* {alert.get('router_display_name')}\n"
        f"• *Estado:* {alert.get('operational_status')}\n"
        f"• *Hora:* {alert.get('timestamp_iso')}"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})


def _dispatch_smtp_sync(config: dict[str, Any], alert: dict[str, Any]) -> None:
    host = config.get("smtp_host", "localhost")
    port = int(config.get("smtp_port", 587))
    user = config.get("smtp_user")
    pwd = config.get("smtp_password")
    to_addrs = config.get("to_addresses", [])

    if not to_addrs:
        return

    msg = EmailMessage()
    msg["Subject"] = f"[RoSGrid] Alerta: {alert.get('event_name')} - {alert.get('router_display_name')}"
    msg["From"] = user or "noreply@rosgrid.local"
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(
        f"Evento: {alert.get('event_name')}\n"
        f"Router: {alert.get('router_display_name')}\n"
        f"Estado: {alert.get('operational_status')}\n"
        f"Timestamp: {alert.get('timestamp_iso')}\n"
    )
    with smtplib.SMTP(host, port, timeout=10) as server:
        if config.get("use_tls", True):
            server.starttls()
        if user and pwd:
            server.login(user, pwd)
        server.send_message(msg)


async def _dispatch_webhook(config: dict[str, Any], alert: dict[str, Any]) -> None:
    webhook_url = config.get("webhook_url")
    secret = config.get("secret", "").encode("utf-8")
    if not webhook_url:
        return

    body = json.dumps(alert).encode("utf-8")
    sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-RoSGrid-Signature-256": sig,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(webhook_url, content=body, headers=headers)


async def _dispatch_to_channel(tenant_id: uuid.UUID, ch: NotificationChannel, alert: dict[str, Any]) -> None:
    event_name = alert.get("event_name", "")
    if event_name not in ch.subscribed_events:
        return

    conf = _decrypt_config(tenant_id, ch)
    try:
        if ch.channel_type == AlertChannelTypeEnum.TELEGRAM_BOT:
            await _dispatch_telegram(conf, alert)
        elif ch.channel_type == AlertChannelTypeEnum.SMTP_EMAIL:
            await asyncio.to_thread(_dispatch_smtp_sync, conf, alert)
        elif ch.channel_type == AlertChannelTypeEnum.GENERIC_WEBHOOK:
            await _dispatch_webhook(conf, alert)
    except Exception as exc:
        logger.error("Fallo al despachar alerta a canal %s: %s", ch.name, exc)


async def _process_alert_payload(tenant_id_str: str, raw_alert: str) -> None:
    try:
        tenant_id = uuid.UUID(tenant_id_str)
        alert = json.loads(raw_alert)
    except Exception as exc:
        logger.error("Error decodificando alerta pub/sub: %s", exc)
        return

    async with async_session_maker() as session:
        stmt = (
            select(NotificationChannel)
            .where(NotificationChannel.tenant_id == tenant_id, NotificationChannel.is_enabled.is_(True))
        )
        channels = (await session.execute(stmt)).scalars().all()
        for ch in channels:
            await _dispatch_to_channel(tenant_id, ch, alert)


async def alert_dispatcher_worker_loop() -> None:
    """Escucha el bus de alertas en Redis y despacha notificaciones a los canales activos."""
    logger.info("Iniciando Worker 2: Despachador Multi-Canal de Alertas...")
    redis = get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("rg:pubsub:alerts:*")

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                raw_ch = msg["channel"].decode("utf-8") if isinstance(msg["channel"], bytes) else msg["channel"]
                tid_str = raw_ch.split(":")[-1]
                raw_data = msg["data"].decode("utf-8") if isinstance(msg["data"], bytes) else msg["data"]
                await _process_alert_payload(tid_str, raw_data)
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.punsubscribe("rg:pubsub:alerts:*")
        await pubsub.close()
