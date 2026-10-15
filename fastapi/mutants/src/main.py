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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await close_redis_client()
mutants_x_create_app__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_create_app__mutmut)
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


def x_create_app__mutmut_orig() -> FastAPI:
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


def x_create_app__mutmut_1() -> FastAPI:
    app = None

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


def x_create_app__mutmut_2() -> FastAPI:
    app = FastAPI(
        title=None,
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


def x_create_app__mutmut_3() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version=None,
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


def x_create_app__mutmut_4() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description=None,
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


def x_create_app__mutmut_5() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        lifespan=None,
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


def x_create_app__mutmut_6() -> FastAPI:
    app = FastAPI(
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


def x_create_app__mutmut_7() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
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


def x_create_app__mutmut_8() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
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


def x_create_app__mutmut_9() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
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


def x_create_app__mutmut_10() -> FastAPI:
    app = FastAPI(
        title="XXRoSGrid APIXX",
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


def x_create_app__mutmut_11() -> FastAPI:
    app = FastAPI(
        title="rosgrid api",
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


def x_create_app__mutmut_12() -> FastAPI:
    app = FastAPI(
        title="ROSGRID API",
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


def x_create_app__mutmut_13() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="XX1.0.0XX",
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


def x_create_app__mutmut_14() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="XXPlataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)XX",
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


def x_create_app__mutmut_15() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="plataforma centralizada multi-tenant para flotas mikrotik routeros v7+ (gpl-3.0-only)",
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


def x_create_app__mutmut_16() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="PLATAFORMA CENTRALIZADA MULTI-TENANT PARA FLOTAS MIKROTIK ROUTEROS V7+ (GPL-3.0-ONLY)",
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


def x_create_app__mutmut_17() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        lifespan=lifespan,
    )

    # 1. Observabilidad obligatoria (Nivel 11X)
    Instrumentator().instrument(app).expose(None)

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


def x_create_app__mutmut_18() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        lifespan=lifespan,
    )

    # 1. Observabilidad obligatoria (Nivel 11X)
    Instrumentator().instrument(None).expose(app)

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


def x_create_app__mutmut_19() -> FastAPI:
    app = FastAPI(
        title="RoSGrid API",
        version="1.0.0",
        description="Plataforma Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (GPL-3.0-only)",
        lifespan=lifespan,
    )

    # 1. Observabilidad obligatoria (Nivel 11X)
    Instrumentator().instrument(app).expose(app)

    # 2. Middlewares de seguridad e infraestructura (orden inverso de ejecución en Starlette)
    app.add_middleware(None)
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


def x_create_app__mutmut_20() -> FastAPI:
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
    app.add_middleware(None)
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


def x_create_app__mutmut_21() -> FastAPI:
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
    app.add_middleware(None)

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


def x_create_app__mutmut_22() -> FastAPI:
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
    app.include_router(None)

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

mutants_x_create_app__mutmut['_mutmut_orig'] = x_create_app__mutmut_orig # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_1'] = x_create_app__mutmut_1 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_2'] = x_create_app__mutmut_2 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_3'] = x_create_app__mutmut_3 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_4'] = x_create_app__mutmut_4 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_5'] = x_create_app__mutmut_5 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_6'] = x_create_app__mutmut_6 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_7'] = x_create_app__mutmut_7 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_8'] = x_create_app__mutmut_8 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_9'] = x_create_app__mutmut_9 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_10'] = x_create_app__mutmut_10 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_11'] = x_create_app__mutmut_11 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_12'] = x_create_app__mutmut_12 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_13'] = x_create_app__mutmut_13 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_14'] = x_create_app__mutmut_14 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_15'] = x_create_app__mutmut_15 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_16'] = x_create_app__mutmut_16 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_17'] = x_create_app__mutmut_17 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_18'] = x_create_app__mutmut_18 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_19'] = x_create_app__mutmut_19 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_20'] = x_create_app__mutmut_20 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_21'] = x_create_app__mutmut_21 # type: ignore # mutmut generated
mutants_x_create_app__mutmut['x_create_app__mutmut_22'] = x_create_app__mutmut_22 # type: ignore # mutmut generated


app = create_app()
