# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from src.models.core import SystemRoleEnum


class LoginStep1Request(BaseModel):
    tenant_slug: str = Field(..., min_length=2, max_length=64)
    email: str | None = None
    username_or_email: str | None = None
    password: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_identifier(self) -> "LoginStep1Request":
        if not self.email and not self.username_or_email:
            raise ValueError("Debe proporcionar 'email' o 'username_or_email'")
        return self

    @property
    def identifier(self) -> str:
        return (self.username_or_email or self.email or "").strip()


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


class BootstrapStatusResponse(BaseModel):
    is_bootstrapped: bool
    tenants_count: int
    users_count: int
    registration_enabled: bool = True
    message: str


class BootstrapInitRequest(BaseModel):
    tenant_name: str = Field(..., min_length=2, max_length=128)
    tenant_slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    admin_username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=12)
    admin_full_name: str = Field(..., min_length=3, max_length=128)


class BootstrapInitResponse(BaseModel):
    status: str
    tenant_id: uuid.UUID
    tenant_slug: str
    admin_id: uuid.UUID
    admin_username: str
    totp_secret: str
    totp_provisioning_uri: str
    backup_codes: list[str]
    challenge_id: str | None = None
    message: str


class RegisterUserRequest(BaseModel):
    tenant_slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=12)


class RegisterUserResponse(BaseModel):
    status: str
    message: str
    user_id: uuid.UUID
    username: str
    is_active: bool
