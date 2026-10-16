# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ROSGRID_ENV: str = "production"
    ROSGRID_HTTP_PORT: int = 8080

    # PostgreSQL
    POSTGRES_DB: str = "rosgrid"
    POSTGRES_USER: str = "rosgrid_user"
    POSTGRES_PASSWORD: str = "cambiar_en_entorno_local"
    ROSGRID_DATABASE_URL: str = "postgresql+asyncpg://rosgrid_user:cambiar_en_entorno_local@rosgrid_db:5432/rosgrid"
    ROSGRID_SYNC_DATABASE_URL: str = "postgresql://rosgrid_user:cambiar_en_entorno_local@rosgrid_db:5432/rosgrid"

    # Redis
    REDIS_PASSWORD: str = "cambiar_en_entorno_local"
    ROSGRID_REDIS_URL: str = "redis://:cambiar_en_entorno_local@rosgrid_redis:6379/0"

    # Criptografía
    ROSGRID_MASTER_VAULT_KEY: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    ROSGRID_JWT_SECRET_KEY: str = "qa_jwt_secret_key_for_ephemeral_testing_only"
    ROSGRID_CSRF_HMAC_SECRET: str = "qa_csrf_hmac_secret_for_ephemeral_testing_only"

    # MikroTik & Operaciones
    ROSGRID_MIKROTIK_TIMEOUT_SECONDS: int = 10
    ROSGRID_SAFEMODE_ROLLBACK_SECONDS: int = 60
    ROSGRID_BACKUP_RETENTION_DAYS: int = 30

    # Model Context Protocol (MCP)
    ROSGRID_MCP_ENABLED: bool = False
    ROSGRID_MCP_RATE_LIMIT_PER_MIN: int = 30


settings = Settings()
