# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Respaldos .rsc/.backup y Comparador Diff estilo Git."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class BackupItemResponse(StrictBaseModel):
    id: uuid.UUID
    backup_type: str
    ros_version_at_backup: str
    rsc_sha256_hash: str
    rsc_size_bytes: int
    diff_lines_added: int
    diff_lines_removed: int
    parent_backup_id: uuid.UUID | None
    has_binary_backup: bool
    created_at: datetime
    last_verified_identical_at: datetime
    expires_at: datetime


class BackupListResponse(StrictBaseModel):
    router_id: uuid.UUID
    retention_days: int
    items: list[BackupItemResponse]


class BackupTriggerResponse(StrictBaseModel):
    status: str
    backup_id: uuid.UUID | None = None
    rsc_sha256_hash: str | None = None
    message: str


class BackupDiffHunk(StrictBaseModel):
    section_header: str | None = None
    old_line_num: int | None = None
    new_line_num: int | None = None
    change_type: str  # ADDED, REMOVED, MODIFIED, UNCHANGED
    old_text: str | None = None
    new_text: str | None = None


class BackupGitDiffResponse(StrictBaseModel):
    router_id: uuid.UUID
    base_backup_id: str
    base_created_at: str | None = None
    target_backup_id: str
    target_created_at: str | None = None
    lines_added: int
    lines_removed: int
    unified_diff_text: str
    side_by_side_hunks: list[BackupDiffHunk] = Field(default_factory=list)
