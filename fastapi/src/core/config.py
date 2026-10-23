# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from pydantic import Field, model_validator
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
    POSTGRES_PASSWORD: str = Field(default_factory=str)
    ROSGRID_DATABASE_URL: str = Field(default_factory=str)
    ROSGRID_SYNC_DATABASE_URL: str = Field(default_factory=str)

    # Redis
    REDIS_PASSWORD: str = Field(default_factory=str)
    ROSGRID_REDIS_URL: str = Field(default_factory=str)

    @model_validator(mode="after")
    def _compute_default_urls(self) -> "Settings":
        self._ensure_database_urls()
        self._ensure_redis_url()
        return self

    def _ensure_database_urls(self) -> None:
        if not self.ROSGRID_DATABASE_URL:
            auth = (
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                if self.POSTGRES_PASSWORD
                else f"{self.POSTGRES_USER}@"
            )
            self.ROSGRID_DATABASE_URL = f"postgresql+asyncpg://{auth}rosgrid_db:5432/{self.POSTGRES_DB}"
        if not self.ROSGRID_SYNC_DATABASE_URL:
            auth = (
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                if self.POSTGRES_PASSWORD
                else f"{self.POSTGRES_USER}@"
            )
            self.ROSGRID_SYNC_DATABASE_URL = f"postgresql://{auth}rosgrid_db:5432/{self.POSTGRES_DB}"

    def _ensure_redis_url(self) -> None:
        if not self.ROSGRID_REDIS_URL:
            auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.ROSGRID_REDIS_URL = f"redis://{auth}rosgrid_redis:6379/0"

    # Criptografía
    ROSGRID_MASTER_VAULT_KEY: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    ROSGRID_JWT_SECRET_KEY: str = "qa_jwt_secret_key_for_ephemeral_testing_only"
    ROSGRID_CSRF_HMAC_SECRET: str = "qa_csrf_hmac_secret_for_ephemeral_testing_only"
    ROSGRID_REFRESH_TOKEN_GRACE_PERIOD_SECONDS: int = 5

    # MikroTik & Operaciones
    ROSGRID_MIKROTIK_TIMEOUT_SECONDS: int = 10
    ROSGRID_SAFEMODE_ROLLBACK_SECONDS: int = 60
    ROSGRID_BACKUP_RETENTION_DAYS: int = 30

    # Model Context Protocol (MCP)
    ROSGRID_MCP_ENABLED: bool = False
    ROSGRID_MCP_RATE_LIMIT_PER_MIN: int = 30

    # Syslog & Telemetría Prometheus (Spec 35)
    ROSGRID_SYSLOG_PORT: int = 5514
    ROSGRID_PROMETHEUS_SCRAPE_TOKEN: str = ""

    # Fuentes Oficiales de Boletines y Vulnerabilidades CVE
    ROSGRID_CVE_PRIMARY_SOURCE: str = "https://mikrotik.com/supportsec"
    ROSGRID_CVE_RSS_SOURCE: str = "https://cdn.mikrotik.com/web-assets/supportsec/rss.xml"
    ROSGRID_CVE_NVD_SEARCH_SOURCE: str = "https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records"

    # Configuración de Orígenes Cruzados (CORS) y Despliegue Separado
    ROSGRID_CORS_ORIGINS: str = "*"
    ROSGRID_CROSS_ORIGIN_COOKIES: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.ROSGRID_CORS_ORIGINS or self.ROSGRID_CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.ROSGRID_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
