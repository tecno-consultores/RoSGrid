# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors


from pydantic import BaseModel, Field


class ActiveSessionItem(BaseModel):
    session_id: str
    user_id: str
    username: str
    full_name: str
    role: str
    ip_address: str
    user_agent: str
    current_router_id: str | None = None
    current_router_name: str | None = None
    current_view_path: str | None = None
    created_at: str
    last_activity_at: str


class ActiveSessionsListResponse(BaseModel):
    total_active_sessions: int
    items: list[ActiveSessionItem]


class TerminateSessionRequest(BaseModel):
    reason: str = Field("Revocación manual por el Administrador", max_length=255)
