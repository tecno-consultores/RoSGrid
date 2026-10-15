# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.deps import get_current_user_claims
from src.api.router import api_v1_router
from src.core.csrf import CSRFProtectionMiddleware
from src.core.security_headers import SecurityHeadersMiddleware
from src.redis_layer.client import close_redis_client
from src.redis_layer.idempotency import IdempotencyMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await close_redis_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        lifespan=lifespan,
    )

    # 1. Observabilidad obligatoria (Nivel 11X)
    Instrumentator().instrument(app).expose(app)

    # 2. Middlewares de seguridad e infraestructura (orden inverso de ejecución en Starlette)
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(CSRFProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Router de API
    app.include_router(api_v1_router)

    # 4. Endpoint de salud
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "rosgrid-api"}

    # 5. Alias /users/me para compatibilidad con suite BDD Karate Labs (api_test.feature)
    @app.get("/users/me", tags=["Compatibility"])
    async def users_me_alias(
        claims: dict[str, Any] = Depends(get_current_user_claims),
    ) -> dict[str, Any]:
        return claims

    return app


app = create_app()
