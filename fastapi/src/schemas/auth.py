# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.core import SystemRoleEnum


class LoginStep1Request(BaseModel):
    tenant_slug: str = Field(..., min_length=2, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginStep1Response(BaseModel):
    challenge_id: str
    tenant_slug: str
    next_step: str  # "VERIFY_2FA_TOTP" | "ENROLL_2FA_REQUIRED"
    totp_provisioning_uri: str | None = None
    expires_in_seconds: int = 180


class Verify2FARequest(BaseModel):
    challenge_id: str
    totp_code: str = Field(..., min_length=6, max_length=10)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: SystemRoleEnum
    tenant_id: uuid.UUID
    tenant_slug: str
    tenant_name: str
    has_all_routers_access: bool


class AuthSessionResponse(BaseModel):
    session_id: str
    user: UserProfileResponse
    csrf_token: str
