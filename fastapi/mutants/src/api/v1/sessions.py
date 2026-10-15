# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import require_roles
from src.models.core import SystemRoleEnum
from src.redis_layer.client import get_redis_client
from src.redis_layer.sessions import (
    kill_all_user_sessions,
    kill_session,
)
from src.schemas.sessions import (
    ActiveSessionItem,
    ActiveSessionsListResponse,
    TerminateSessionRequest,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@router.get("/active", response_model=ActiveSessionsListResponse)
async def list_active_sessions(
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.AUDITOR,
        )
    ),
) -> ActiveSessionsListResponse:
    tenant_id = claims["tid"]
    redis = get_redis_client()
    session_ids = await redis.zrange(f"rg:{tenant_id}:active_sessions", 0, -1)

    items: list[ActiveSessionItem] = []
    for sid in session_ids:
        sid_str = sid.decode("utf-8") if isinstance(sid, bytes) else str(sid)
        sess_data = await redis.hgetall(f"rg:{tenant_id}:sess:{sid_str}")
        if sess_data:
            items.append(
                ActiveSessionItem(
                    session_id=str(sess_data.get("session_id", sid_str)),
                    user_id=str(sess_data.get("user_id", "")),
                    username=str(sess_data.get("username", "")),
                    full_name=str(sess_data.get("full_name", "")),
                    role=str(sess_data.get("role", "")),
                    ip_address=str(sess_data.get("ip_address", "")),
                    user_agent=str(sess_data.get("user_agent", "")),
                    current_router_id=str(sess_data.get("current_router_id"))
                    if sess_data.get("current_router_id")
                    else None,
                    current_router_name=str(sess_data.get("current_router_name"))
                    if sess_data.get("current_router_name")
                    else None,
                    current_view_path=str(sess_data.get("current_view_path"))
                    if sess_data.get("current_view_path")
                    else None,
                    created_at=str(sess_data.get("created_at", "")),
                    last_activity_at=str(sess_data.get("last_activity_at", "")),
                )
            )

    return ActiveSessionsListResponse(total_active_sessions=len(items), items=items)


@router.delete("/{session_id}")
async def terminate_session(
    session_id: str,
    body: TerminateSessionRequest | None = None,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
        )
    ),
) -> dict[str, str]:
    tenant_id = claims["tid"]
    reason = body.reason if body else "Revocación manual por el Administrador"
    success = await kill_session(tenant_id, session_id, killed_by=claims["sub"], reason=reason)
    if not success:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o ya finalizada")
    return {"status": "terminated", "session_id": session_id}


@router.delete("/user/{user_id}/all")
async def terminate_all_user_sessions(
    user_id: uuid.UUID,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
        )
    ),
) -> dict[str, Any]:
    tenant_id = claims["tid"]
    count = await kill_all_user_sessions(
        tenant_id, str(user_id), killed_by=claims["sub"], reason="Revocación global de sesiones"
    )
    return {"status": "terminated_all", "revoked_count": count}
