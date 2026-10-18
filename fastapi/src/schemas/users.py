# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from src.models.core import SystemRoleEnum


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    full_name: str = Field(default="", max_length=150)
    temporary_password: str | None = Field(None, min_length=8)
    password: str | None = Field(None, min_length=8)
    role: SystemRoleEnum
    has_all_routers_access: bool = False
    allowed_cidr_list: list[str] = Field(default_factory=list)

    @field_validator("allowed_cidr_list", mode="before")
    @classmethod
    def normalize_cidr_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @model_validator(mode="after")
    def validate_password_and_fullname(self) -> "CreateUserRequest":
        if not self.temporary_password and not self.password:
            raise ValueError(
                "Se requiere una contraseña temporal ('temporary_password' o 'password') de al menos 8 caracteres."
            )
        if not self.temporary_password:
            self.temporary_password = self.password
        if not self.full_name or not self.full_name.strip():
            self.full_name = self.username
        return self


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(None, min_length=3, max_length=150)
    role: SystemRoleEnum | None = None
    is_active: bool | None = None
    is_locked: bool | None = None
    has_all_routers_access: bool | None = None
    allowed_cidr_list: list[str] | None = None


class RouterAssignmentItem(BaseModel):
    router_id: uuid.UUID
    can_read: bool = True
    can_write_layer1: bool = False
    can_write_layer2: bool = False
    can_execute_diagnostics: bool = True
    can_trigger_backup: bool = False
    can_reboot: bool = False
    bypass_maker_checker: bool = False


class AssignUserRoutersRequest(BaseModel):
    has_all_routers_access: bool = False
    router_assignments: list[RouterAssignmentItem] = Field(default_factory=list)
    permissions: list[RouterAssignmentItem] | None = None

    @model_validator(mode="after")
    def unify_assignments(self) -> "AssignUserRoutersRequest":
        if not self.router_assignments and self.permissions:
            self.router_assignments = self.permissions
        return self



class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: SystemRoleEnum
    is_active: bool
    is_locked: bool
    failed_login_attempts: int
    totp_enabled: bool
    has_all_routers_access: bool
    allowed_cidr_list: list[str]
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
