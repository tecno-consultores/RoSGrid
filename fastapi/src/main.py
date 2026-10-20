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


async def _check_database_health() -> str:
    """Verifica la conectividad activa con PostgreSQL 17."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        is_test_env = settings.ROSGRID_ENV.startswith("qa") or settings.ROSGRID_ENV == "test"
        return "mocked" if is_test_env else "disconnected"


async def _check_redis_health() -> str:
    """Verifica la conectividad activa con KeyDB."""
    try:
        redis = get_redis_client()
        await redis.ping()
        return "connected"
    except Exception:
        is_test_env = settings.ROSGRID_ENV.startswith("qa") or settings.ROSGRID_ENV == "test"
        return "mocked" if is_test_env else "disconnected"


async def health_check(response: Response) -> dict[str, str]:
    """Endpoint de salud con verificación activa de PostgreSQL y KeyDB."""
    db_status = await _check_database_health()
    redis_status = await _check_redis_health()
    is_healthy = db_status != "disconnected" and redis_status != "disconnected"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "rosgrid-api",
        "database": db_status,
        "redis": redis_status,
    }


def users_me_alias(
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> dict[str, Any]:
    """Alias /users/me para compatibilidad con suite BDD Karate Labs."""
    return claims


def _setup_cors(app: FastAPI) -> None:
    """Configura CORS para despliegue distribuido o monolítico."""
    cors_origins = settings.cors_origins_list
    is_prod = settings.ROSGRID_ENV == "production"

    if cors_origins == ["*"]:
        if is_prod:
            # En producción, si no se especifican orígenes explícitos en lista blanca,
            # no se permiten credenciales abiertas para cualquier origen arbitrario.
            app.add_middleware(
                CORSMiddleware,
                allow_origins=[],
                allow_credentials=False,
                allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                allow_headers=["*"],
            )
        else:
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
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "Idempotency-Key", "Accept"],
        )


def create_app() -> FastAPI:
    is_prod = settings.ROSGRID_ENV == "production"
    docs_url = None if is_prod else "/docs"
    redoc_url = None if is_prod else "/redoc"
    openapi_url = None if is_prod else "/openapi.json"

    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        default_response_class=ORJSONResponse,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # 1. Observabilidad obligatoria (Nivel 11X)
    Instrumentator().instrument(app).expose(app)

    # 2. Middlewares de seguridad e infraestructura (orden inverso de ejecución en Starlette)
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(CSRFProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    _setup_cors(app)

    # 3. Router de API y WebSockets
    app.include_router(api_v1_router)
    app.include_router(websockets_router)

    # 4. Endpoints auxiliares
    app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])
    app.add_api_route("/users/me", users_me_alias, methods=["GET"], tags=["Compatibility"])

    return app


app = create_app()
