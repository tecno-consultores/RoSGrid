# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para la Consola Forense de Auditoría Inmutable y Verificación WORM."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class AuditLogResponse(StrictBaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    actor_user_id: uuid.UUID | None
    actor_username: str
    actor_role: str
    actor_ip: str
    actor_user_agent: str | None
    event_category: str
    event_action: str
    router_id: uuid.UUID | None
    router_display_name: str | None
    ros_rest_method: str | None
    ros_rest_endpoint: str | None
    idempotency_key: str | None
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    status_code: int
    error_message: str | None
    prev_record_hash: str
    record_sha256_hash: str
    created_at: datetime


class AuditLogListResponse(StrictBaseModel):
    total: int
    limit: int
    offset: int
    items: list[AuditLogResponse] = Field(default_factory=list)


class AuditVerifyIntegrityResponse(StrictBaseModel):
    integrity_status: str  # "VERIFIED_INTACT" | "COMPROMISED"
    verified_records_count: int
    corrupted_record_id: uuid.UUID | None = None
    message: str
