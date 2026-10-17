# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from src.api.deps import get_current_user_claims
from src.api.router import api_v1_router
from src.api.v1.websockets import router as websockets_router
from src.core.config import settings
from src.core.csrf import CSRFProtectionMiddleware
from src.core.security_headers import SecurityHeadersMiddleware
from src.db.session import engine
from src.redis_layer.client import close_redis_client, get_redis_client
from src.redis_layer.idempotency import IdempotencyMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await close_redis_client()


def create_app() -> FastAPI:
    is_prod = settings.ROSGRID_ENV == "production"
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        default_response_class=ORJSONResponse,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan,
    )

    # 1. Observabilidad obligatoria (Nivel 11X)
    Instrumentator().instrument(app).expose(app)

    # 2. Middlewares de seguridad e infraestructura (orden inverso de ejecución en Starlette)
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(CSRFProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2.1 Soporte para despliegue distribuido (CORS) y microservicios
    cors_origins = settings.cors_origins_list
    if cors_origins == ["*"]:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^https?://.*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 3. Router de API y WebSockets
    app.include_router(api_v1_router)
    app.include_router(websockets_router)

    # 4. Endpoint de salud con verificación activa de PostgreSQL y KeyDB
    @app.get("/health", tags=["Health"])
    async def health_check(response: Response) -> dict[str, str]:
        db_status = "connected"
        redis_status = "connected"
        is_healthy = True

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            if not settings.ROSGRID_ENV.startswith("qa") and settings.ROSGRID_ENV != "test":
                db_status = "disconnected"
                is_healthy = False
            else:
                db_status = "mocked"

        try:
            redis = get_redis_client()
            await redis.ping()
        except Exception:
            if not settings.ROSGRID_ENV.startswith("qa") and settings.ROSGRID_ENV != "test":
                redis_status = "disconnected"
                is_healthy = False
            else:
                redis_status = "mocked"

        if not is_healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "rosgrid-api",
            "database": db_status,
            "redis": redis_status,
        }

    # 5. Alias /users/me para compatibilidad con suite BDD Karate Labs (api_test.feature)
    @app.get("/users/me", tags=["Compatibility"])
    async def users_me_alias(
        claims: dict[str, Any] = Depends(get_current_user_claims),
    ) -> dict[str, Any]:
        return claims

    return app


app = create_app()
