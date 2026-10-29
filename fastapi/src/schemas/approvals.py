# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para la Bandeja de Aprobaciones Maker-Checker."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class ApprovalRequestResponse(StrictBaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID | None
    router_name: str | None = None
    action_type: str
    status: str
    summary: str
    requester_justification: str
    ros_rest_method: str
    ros_rest_path: str
    request_payload: dict[str, Any]
    previous_state_snapshot: dict[str, Any] | None
    requested_by: uuid.UUID
    requested_by_username: str | None = None
    requested_by_role: str | None = None
    reviewed_by: uuid.UUID | None
    review_comment: str | None
    expires_at: datetime
    reviewed_at: datetime | None
    executed_at: datetime | None
    execution_result: dict[str, Any] | None
    created_at: datetime


class ApprovalListResponse(StrictBaseModel):
    total: int
    items: list[ApprovalRequestResponse]


class ApproveRequestPayload(StrictBaseModel):
    review_comment: str | None = Field(default=None, min_length=1, max_length=1000)
    comment: str | None = Field(default=None, min_length=1, max_length=1000)
    totp_code: str | None = Field(default=None, max_length=16)
    decision: str | None = None

    @model_validator(mode="after")
    def _normalize_comment(self) -> "ApproveRequestPayload":
        resolved = (self.review_comment or self.comment or "Aprobado por operador nivel 3 / administrador").strip()
        self.review_comment = resolved
        return self


class RejectRequestPayload(StrictBaseModel):
    review_comment: str | None = Field(default=None, min_length=1, max_length=1000)
    comment: str | None = Field(default=None, min_length=1, max_length=1000)
    totp_code: str | None = Field(default=None, max_length=16)
    decision: str | None = None

    @model_validator(mode="after")
    def _normalize_comment(self) -> "RejectRequestPayload":
        resolved = (self.review_comment or self.comment or "Rechazado por operador nivel 3 / administrador").strip()
        self.review_comment = resolved
        return self
