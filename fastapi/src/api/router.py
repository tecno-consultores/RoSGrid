# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.sessions import router as sessions_router
from src.api.v1.tenants import router as tenants_router
from src.api.v1.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(tenants_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(sessions_router)
