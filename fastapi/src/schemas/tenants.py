# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.core import TenantStatusEnum


class CreateTenantRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(..., min_length=2, max_length=150)
    tax_id: str | None = Field(None, max_length=64)
    max_routers_quota: int = Field(100, gt=0)
    max_users_quota: int = Field(50, gt=0)
    require_2fa_all_users: bool = True
    default_safemode_seconds: int = Field(60, ge=15, le=300)

    # Administrador inicial del tenant
    admin_username: str = Field(..., min_length=3, max_length=64)
    admin_email: EmailStr
    admin_full_name: str = Field(..., min_length=3, max_length=150)
    admin_password: str = Field(..., min_length=8)


class UpdateTenantRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    tax_id: str | None = None
    status: TenantStatusEnum | None = None
    max_routers_quota: int | None = Field(None, gt=0)
    max_users_quota: int | None = Field(None, gt=0)
    require_2fa_all_users: bool | None = None
    default_safemode_seconds: int | None = Field(None, ge=15, le=300)


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    tax_id: str | None
    status: TenantStatusEnum
    max_routers_quota: int
    max_users_quota: int
    require_2fa_all_users: bool
    default_safemode_seconds: int
    created_at: datetime
    updated_at: datetime
