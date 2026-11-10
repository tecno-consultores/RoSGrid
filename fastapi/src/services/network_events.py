# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Servicio centralizado de emisión de eventos técnicos de red y webhooks salientes."""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from src.core.ssrf import is_safe_outbound_url, is_safe_outbound_url_async
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)

_BLOCKED_OUTBOUND_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "::1",
    "0.0.0.0",  # nosec B104
    "169.254.169.254",
    "metadata.google.internal",
    "localtest.me",
    "rosgrid-db",
    "rosgrid_db",
    "rosgrid-redis",
    "rosgrid_redis",
    "rosgrid-api",
    "rosgrid_api",
    "rosgrid-worker",
    "rosgrid_worker",
    "rosgrid-frontend",
    "rosgrid_frontend",
    "db",
    "redis",
    "keydb",
    "postgres",
}


def is_safe_outbound_service_url(
    url: str,
    *,
    allow_private_cidrs: list[str] | None = None,
) -> bool:
    """Valida que un webhook o destino HTTP saliente no apunte a loopback, link-local, rangos privados o contenedores internos."""
    return is_safe_outbound_url(url, allow_private_cidrs=allow_private_cidrs, resolve_dns=True)


async def publish_network_service_event(
    tenant_id: uuid.UUID,
    event_name: str,
    payload: dict[str, Any],
) -> None:
    """Publica un evento técnico de red hacia el bus de alertas y webhooks de Redis."""
    try:
        redis = get_redis_client()
        event_body = {
            "event_name": event_name,
            "tenant_id": str(tenant_id),
            "timestamp_iso": datetime.now(UTC).isoformat(),
            **payload,
        }
        channel = f"rg:pubsub:alerts:{tenant_id}"
        await redis.publish(channel, json.dumps(event_body))
        logger.info("Evento de red publicado en %s: %s", channel, event_name)
    except Exception as exc:
        logger.warning("Fallo al publicar evento de red %s en Redis: %s", event_name, exc)


async def send_signed_webhook_payload(
    webhook_url: str,
    secret: str,
    event_name: str,
    payload: dict[str, Any],
    timeout: float = 10.0,
) -> bool:
    """Envía un webhook HTTP POST firmado con HMAC-SHA256 según estándar RoSGrid."""
    if not await is_safe_outbound_url_async(webhook_url, allow_private_cidrs=[]):
        logger.warning("Webhook saliente rechazado por validación anti-SSRF: %s", webhook_url)
        return False
    body_data = {
        "event": event_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    body_bytes = json.dumps(body_data).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-RoSGrid-Signature": f"sha256={sig}",
        "X-RoSGrid-Signature-256": sig,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(webhook_url, content=body_bytes, headers=headers)
            return resp.is_success
    except Exception as exc:
        logger.error("Error despachando webhook firmado a %s: %s", webhook_url, exc)
        return False
