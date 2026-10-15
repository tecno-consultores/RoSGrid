# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Canales de Notificación y Despacho de Alertas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class NotificationChannelCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    channel_type: str = Field(..., pattern="^(TELEGRAM_BOT|SMTP_EMAIL|GENERIC_WEBHOOK)$")
    is_enabled: bool = True
    config: dict[str, Any] = Field(..., min_length=1)
    subscribed_events: list[str] = Field(
        default_factory=lambda: ["ROUTER_OFFLINE", "ROUTER_ONLINE", "DEGRADED_HIGH_LOAD", "SSL_MISMATCH"]
    )


class NotificationChannelUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_enabled: bool | None = None
    config: dict[str, Any] | None = None
    subscribed_events: list[str] | None = None


class NotificationChannelResponse(StrictBaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    channel_type: str
    is_enabled: bool
    subscribed_events: list[str]
    created_at: datetime
    updated_at: datetime


class NotificationTestRequest(StrictBaseModel):
    message: str | None = Field(default="Mensaje de prueba de notificación RoSGrid")


class NotificationTestResponse(StrictBaseModel):
    status: str
    detail: str
