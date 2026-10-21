# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Plantillas (Golden Configs), Trabajos Masivos y Actualizador RouterOS v7."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# PLANTILLAS (GOLDEN CONFIGS)
# ============================================================================


class ConfigTemplateCreateRequest(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1)
    variables_schema: list[dict[str, Any]] = Field(default_factory=list)
    rest_steps_template: list[dict[str, Any]] = Field(..., min_length=1)
    requires_safemode: bool = True


class ConfigTemplateUpdateRequest(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    variables_schema: list[dict[str, Any]] | None = None
    rest_steps_template: list[dict[str, Any]] | None = None
    requires_safemode: bool | None = None


class ConfigTemplateResponse(StrictBaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    category: str
    description: str
    variables_schema: list[dict[str, Any]]
    rest_steps_template: list[dict[str, Any]]
    requires_safemode: bool
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class TemplateRenderPreviewRequest(StrictBaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)


class TemplateRenderPreviewResponse(StrictBaseModel):
    rendered_steps: list[dict[str, Any]] = Field(default_factory=list)


class ConfigTemplatePresetResponse(StrictBaseModel):
    name: str
    category: str
    description: str
    variables_schema: list[dict[str, Any]]
    rest_steps_template: list[dict[str, Any]]
    requires_safemode: bool
    ros_command_template: str | None = None


# ============================================================================
# TRABAJOS MASIVOS MULTI-ROUTER (BULK JOBS)
# ============================================================================


class BulkJobCreateRequest(StrictBaseModel):
    job_type: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=180)
    template_id: uuid.UUID | None = None
    execution_parameters: dict[str, Any] = Field(default_factory=dict)
    target_router_ids: list[str] | None = None
    target_role: str | None = None
    target_tag: str | None = None


class BulkJobItemResponse(StrictBaseModel):
    id: uuid.UUID
    router_id: uuid.UUID
    router_display_name: str | None = None
    status: str
    response_summary: dict[str, Any] | None = None
    error_detail: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class BulkJobDetailResponse(StrictBaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    job_type: str
    title: str
    status: str
    template_id: uuid.UUID | None
    execution_parameters: dict[str, Any]
    target_router_ids: list[str]
    total_routers: int
    succeeded_count: int
    failed_count: int
    approval_request_id: uuid.UUID | None
    created_by: uuid.UUID
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    items: list[BulkJobItemResponse] = Field(default_factory=list)


# ============================================================================
# ACTUALIZACIÓN CENTRALIZADA DE ROUTEROS v7 Y ROUTERBOOT
# ============================================================================


class RosUpdateRouterStatus(StrictBaseModel):
    router_id: uuid.UUID
    display_name: str
    ros_version: str | None
    update_available_version: str | None
    firmware_version: str | None
    upgrade_firmware_version: str | None
    has_update: bool


class RosFleetUpdateStatusResponse(StrictBaseModel):
    total_routers: int
    up_to_date_count: int
    pending_update_count: int
    routers: list[RosUpdateRouterStatus] = Field(default_factory=list)


class RosUpdateExecuteRequest(StrictBaseModel):
    router_ids: list[uuid.UUID] = Field(..., min_length=1)
    auto_upgrade_firmware: bool = True
    poe_aware: bool = False
    safety_stop_threshold_percent: float = Field(1.0, ge=0.1, le=100.0)


class RosUpdateExecuteResponse(StrictBaseModel):
    status: str
    message: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    poe_stages: list[list[str]] | None = None
    safety_stop_triggered: bool = False
