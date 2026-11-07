# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Worker 2: Despachador Multi-Canal de Alertas (Telegram, SMTP, Webhook firmado y Wallboard NOC)."""

import asyncio
import hashlib
import hmac
import ipaddress
import json
import logging
import smtplib
import urllib.parse
import uuid
from email.message import EmailMessage
from typing import Any, cast

import httpx
from sqlalchemy import select

from src.core.crypto import decrypt_aes_gcm
from src.db.session import async_session_maker
from src.models.operations import AlertChannelTypeEnum, NotificationChannel
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)


def _decrypt_config(tenant_id: uuid.UUID, ch: NotificationChannel) -> dict[str, Any]:
    aad = f"{tenant_id}:{ch.id}".encode()
    raw = decrypt_aes_gcm(ch.config_ciphertext, ch.config_iv, ch.config_tag, aad)
    return cast(dict[str, Any], json.loads(raw.decode("utf-8")))


async def _dispatch_telegram(config: dict[str, Any], alert: dict[str, Any]) -> None:
    bot_token = config.get("bot_token")
    chat_id = config.get("chat_id")
    if not bot_token or not chat_id:
        return

    custom_msg = alert.get("custom_message")
    if custom_msg:
        text = (
            f"🚨 *Prueba de Alerta RoSGrid*\n"
            f"• *Mensaje:* {custom_msg}\n"
            f"• *Canal:* {alert.get('channel_name', 'Telegram')}\n"
            f"• *Hora:* {alert.get('timestamp_iso')}"
        )
    else:
        text = (
            f"🚨 *Alerta RoSGrid*\n"
            f"• *Evento:* `{alert.get('event_name')}`\n"
            f"• *Router:* {alert.get('router_display_name')}\n"
            f"• *Estado:* {alert.get('operational_status')}\n"
            f"• *Hora:* {alert.get('timestamp_iso')}"
        )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        if hasattr(resp, "raise_for_status") and callable(resp.raise_for_status):
            status_res = resp.raise_for_status()
            if asyncio.iscoroutine(status_res):
                await status_res


def _resolve_smtp_recipients(config: dict[str, Any]) -> list[str]:
    """Extrae la lista de destinatarios desde 'to_emails', 'to_addresses' o fallback a 'from_email'/'smtp_user'."""
    raw_to = config.get("to_emails") or config.get("to_addresses") or []
    if isinstance(raw_to, str):
        recipients = [addr.strip() for addr in raw_to.split(",") if addr.strip()]
    elif isinstance(raw_to, list):
        recipients = [str(addr).strip() for addr in raw_to if str(addr).strip()]
    else:
        recipients = []
    if not recipients:
        fallback = str(config.get("from_email") or config.get("smtp_user") or "").strip()
        if "@" in fallback:
            recipients = [fallback]
    return recipients


def _dispatch_smtp_sync(config: dict[str, Any], alert: dict[str, Any]) -> None:
    host = str(config.get("smtp_host") or "localhost").strip()
    port = int(config.get("smtp_port") or 587)
    user = str(config.get("smtp_user") or "").strip()
    pwd = str(config.get("smtp_password") or "")
    from_addr = str(config.get("from_email") or user or "noreply@rosgrid.local").strip()
    to_addrs = _resolve_smtp_recipients(config)

    if not to_addrs:
        raise ValueError("No se especificaron destinatarios de correo ('to_emails').")

    if "gmail.com" in host.lower() or "googlemail.com" in host.lower():
        pwd_no_spaces = pwd.replace(" ", "")
        if len(pwd_no_spaces) == 16:
            pwd = pwd_no_spaces

    msg = EmailMessage()
    custom_msg = alert.get("custom_message")
    msg["Subject"] = (
        f"[RoSGrid] Prueba de Canal SMTP: {alert.get('channel_name', 'NOC')}"
        if custom_msg
        else f"[RoSGrid] Alerta: {alert.get('event_name')} - {alert.get('router_display_name')}"
    )
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    body_lines = [
        f"Mensaje: {custom_msg}" if custom_msg else f"Evento: {alert.get('event_name')}",
        f"Router: {alert.get('router_display_name', 'N/A')}",
        f"Estado: {alert.get('operational_status', 'TEST')}",
        f"Timestamp: {alert.get('timestamp_iso', '')}",
    ]
    msg.set_content("\n".join(body_lines) + "\n")

    smtp_cls = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
    with smtp_cls(host, port, timeout=12) as server:
        server.ehlo()
        if port != 465 and config.get("use_tls", True):
            server.starttls()
            server.ehlo()
        if user and pwd:
            server.login(user, pwd)
        server.send_message(msg)


def is_safe_webhook_url(url: str) -> bool:
    """Verifica que la URL no apunte a esquemas no válidos o direcciones IP privadas / locales (Anti-SSRF)."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").strip().lower()
        if not hostname or hostname in ("localhost", "127.0.0.1", "::1"):
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False


async def _dispatch_webhook(config: dict[str, Any], alert: dict[str, Any]) -> None:
    webhook_url = config.get("webhook_url")
    secret = config.get("secret", "").encode("utf-8")
    if not webhook_url:
        return
    if not is_safe_webhook_url(webhook_url):
        logger.warning("Despacho de webhook cancelado por validación de seguridad SSRF: %s", webhook_url)
        return

    body = json.dumps(alert).encode("utf-8")
    sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-RoSGrid-Signature": f"sha256={sig}",
        "X-RoSGrid-Signature-256": sig,
    }
    auth_header = str(config.get("auth_header") or "").strip()
    if auth_header:
        headers["Authorization"] = auth_header

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, content=body, headers=headers)
        if hasattr(resp, "raise_for_status") and callable(resp.raise_for_status):
            status_res = resp.raise_for_status()
            if asyncio.iscoroutine(status_res):
                await status_res


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
        stmt = select(NotificationChannel).where(
            NotificationChannel.tenant_id == tenant_id, NotificationChannel.is_enabled.is_(True)
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
