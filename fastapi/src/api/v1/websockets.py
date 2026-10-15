# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints WebSocket: Telemetría Efímera WinBox y Eventos Globales del Tenant con Kill-Switch."""

import asyncio
import json
import logging
import uuid
from typing import Any

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from src.core.config import settings
from src.db.session import async_session_maker
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.redis_layer.client import get_redis_client
from src.services.telemetry_multiplexer import (
    cancel_poller_task,
    ensure_poller_active,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws/v1", tags=["WebSockets"])

_GLOBAL_ACCESS_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    SystemRoleEnum.TENANT_ADMIN.value,
    SystemRoleEnum.SUPERVISOR.value,
    SystemRoleEnum.INVENTORY_MANAGER.value,
    SystemRoleEnum.AUDITOR.value,
    SystemRoleEnum.NOC_MONITOR.value,
}


async def _extract_ws_claims(ws: WebSocket) -> dict[str, Any]:
    token = ws.cookies.get("__Host-rg_at") or ws.cookies.get("rg_at")
    if not token:
        await ws.close(code=4401, reason="No autenticado (falta cookie de sesión)")
        raise WebSocketDisconnect(code=4401)

    try:
        payload = jwt.decode(token, settings.ROSGRID_JWT_SECRET_KEY, algorithms=["HS256"])
    except Exception as exc:
        await ws.close(code=4401, reason=f"Token inválido: {exc}")
        raise WebSocketDisconnect(code=4401) from exc

    tenant_id = payload.get("tid")
    session_id = payload.get("sid")
    if not tenant_id or not session_id:
        await ws.close(code=4401, reason="Token malformado")
        raise WebSocketDisconnect(code=4401)

    redis = get_redis_client()
    sess_alive = await redis.exists(f"rg:{tenant_id}:sess:{session_id}")
    if not sess_alive:
        await ws.close(code=4401, reason="Sesión revocada o expirada")
        raise WebSocketDisconnect(code=4401)

    return payload


async def _verify_ws_router_permission(claims: dict[str, Any], router_id: uuid.UUID) -> None:
    role = claims.get("rol")
    if role in _GLOBAL_ACCESS_ROLES or claims.get("all_r", False):
        return

    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    async with async_session_maker() as session:
        stmt = select(UserRouterPermission).where(
            UserRouterPermission.tenant_id == tenant_id,
            UserRouterPermission.user_id == user_id,
            UserRouterPermission.router_id == router_id,
            UserRouterPermission.can_read.is_(True),
        )
        perm = (await session.execute(stmt)).scalar_one_or_none()
        if not perm:
            raise PermissionError("Permiso insuficiente para monitorear este router")


async def _handle_telemetry_msg(ws: WebSocket, channel: str, raw_data: str, sid: str, uid: str) -> bool:
    if "events" in channel:
        try:
            event = json.loads(raw_data)
            if event.get("event_name") == "SESSION_KILLED":
                p = event.get("payload", {})
                if p.get("target_session_id") == sid or p.get("target_user_id") == uid:
                    await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                    return False
        except Exception as exc:
            logger.debug("Error processing telemetry websocket event: %s", exc)
        return True

    await ws.send_text(raw_data)
    return True


@router.websocket("/routers/{router_id}/live-telemetry")
async def router_live_telemetry_ws(ws: WebSocket, router_id: uuid.UUID) -> None:
    """Canal WebSocket para telemetría efímera en vivo (estilo WinBox) con Cero Almacenamiento."""
    await ws.accept()
    claims = await _extract_ws_claims(ws)
    try:
        await _verify_ws_router_permission(claims, router_id)
    except PermissionError:
        await ws.close(code=4403, reason="Sin permiso de lectura sobre este router")
        return

    tenant_id = uuid.UUID(claims["tid"])
    session_id = str(claims["sid"])
    user_id = str(claims["sub"])
    conn_id = str(uuid.uuid4())

    redis = get_redis_client()
    subs_key = f"rg:{tenant_id}:ws_subs:{router_id}"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"
    telem_ch = f"rg:pubsub:telemetry:{tenant_id}:{router_id}"
    event_ch = f"rg:pubsub:events:{tenant_id}"

    await redis.hset(sess_key, "current_router_id", str(router_id))
    await redis.sadd(subs_key, conn_id)
    ensure_poller_active(tenant_id, router_id)

    pubsub = redis.pubsub()
    await pubsub.subscribe(telem_ch, event_ch)

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                raw_str = msg["data"] if isinstance(msg["data"], str) else msg["data"].decode("utf-8")
                keep_going = await _handle_telemetry_msg(ws, msg.get("channel", ""), raw_str, session_id, user_id)
                if not keep_going:
                    break
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        logger.debug("WebSocket live-telemetry disconnected: conn=%s", conn_id)
    finally:
        await pubsub.unsubscribe(telem_ch, event_ch)
        await pubsub.close()
        await redis.srem(subs_key, conn_id)
        await redis.hdel(sess_key, "current_router_id")
        remaining = await redis.scard(subs_key)
        if remaining <= 0:
            cancel_poller_task(tenant_id, router_id)


@router.websocket("/tenant/events")
async def tenant_events_ws(ws: WebSocket) -> None:
    """Canal WebSocket global para eventos NOC, progreso de tareas masivas y Kill-Switch."""
    await ws.accept()
    claims = await _extract_ws_claims(ws)

    tenant_id = uuid.UUID(claims["tid"])
    session_id = str(claims["sid"])
    user_id = str(claims["sub"])

    redis = get_redis_client()
    event_ch = f"rg:pubsub:events:{tenant_id}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(event_ch)

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                raw_str = msg["data"] if isinstance(msg["data"], str) else msg["data"].decode("utf-8")
                try:
                    ev = json.loads(raw_str)
                    if ev.get("event_name") == "SESSION_KILLED":
                        p = ev.get("payload", {})
                        if p.get("target_session_id") == session_id or p.get("target_user_id") == user_id:
                            await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                            break
                except Exception as exc:
                    logger.debug("Error checking kill switch event: %s", exc)
                await ws.send_text(raw_str)
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        logger.debug("WebSocket tenant_events disconnected: session=%s", session_id)
    finally:
        await pubsub.unsubscribe(event_ch)
        await pubsub.close()
