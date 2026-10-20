# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Inventario MikroTik, CSV, Bóveda Step-Up y Mantenimiento."""

import ipaddress
import uuid
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.inventory import (
    RouterAdminStateEnum,
    SSLTrustStatusEnum,
)


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# INVENTARIO DE ROUTERS MIKROTIK
# ============================================================================


class CustomNetworkRoleCreate(StrictBaseModel):
    role_name: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=255)


class CustomNetworkRoleItem(StrictBaseModel):
    id: uuid.UUID
    role_name: str
    description: str | None = None
    created_at: datetime


class NetworkRolesListResponse(StrictBaseModel):
    roles: list[str]
    custom_roles: list[CustomNetworkRoleItem]


_BLOCKED_ROUTER_HOSTS = {
    "localhost",
    "rosgrid-db",
    "rosgrid-redis",
    "rosgrid-api",
    "rosgrid-worker",
    "rosgrid-keydb",
}


def _verify_host_ssrf(host: str) -> None:
    host_lower = host.lower()
    if host_lower in _BLOCKED_ROUTER_HOSTS or host_lower.endswith((".local", ".internal")):
        raise ValueError(f"Host de infraestructura interna no permitido para routers: '{host}'")

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_loopback:
            raise ValueError(f"Dirección loopback no permitida para routers: '{host}'")
        if ip.is_link_local:
            raise ValueError(f"Dirección link-local / metadatos cloud no permitida para routers: '{host}'")
    except ValueError as err:
        if "no permitida" in str(err):
            raise err


def validate_router_target_url(v: str | None) -> str | None:
    """Valida la URL/IP destino del router bloqueando SSRF hacia loopback, metadatos e infra interna."""
    if not v or not v.strip():
        return v
    v_str = v.strip()
    parsed = urlparse(v_str if "://" in v_str else f"https://{v_str}")
    host = (parsed.hostname or v_str).strip()
    if host:
        _verify_host_ssrf(host)
    return v


class CreateRouterRequest(StrictBaseModel):
    display_name: str = Field(..., min_length=2, max_length=120)
    api_base_url: str = Field(..., min_length=5, max_length=255)
    api_port: int = Field(default=443, ge=1, le=65535)
    api_username: str = Field(default="rosgrid_api_admin", min_length=1, max_length=64)
    api_password: str = Field(..., min_length=1)
    network_role: str = Field(..., min_length=2, max_length=64)
    admin_state: RouterAdminStateEnum = RouterAdminStateEnum.PRODUCTION
    physical_location: str = Field(..., min_length=2, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    online_since_date: date
    serial_number: str = Field(..., min_length=1, max_length=64)
    tags: list[str] = Field(default_factory=list)
    operational_notes: str | None = None
    site_contact_info: str | None = Field(default=None, max_length=255)
    auto_rotate_credentials: bool = True
    rotation_interval_days: int = Field(default=30, ge=1, le=365)
    connect_and_discover_now: bool = True

    @field_validator("api_base_url")
    @classmethod
    def check_api_base_url(cls, v: str) -> str:
        return validate_router_target_url(v) or v


class UpdateRouterRequest(StrictBaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=120)
    api_base_url: str | None = Field(default=None, min_length=5, max_length=255)
    api_port: int | None = Field(default=None, ge=1, le=65535)
    network_role: str | None = Field(default=None, min_length=2, max_length=64)
    admin_state: RouterAdminStateEnum | None = None
    physical_location: str | None = Field(default=None, min_length=2, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    online_since_date: date | None = None
    serial_number: str | None = Field(default=None, min_length=1, max_length=64)
    tags: list[str] | None = None
    operational_notes: str | None = None
    site_contact_info: str | None = Field(default=None, max_length=255)
    auto_rotate_credentials: bool | None = None
    rotation_interval_days: int | None = Field(default=None, ge=1, le=365)

    @field_validator("api_base_url")
    @classmethod
    def check_api_base_url(cls, v: str | None) -> str | None:
        return validate_router_target_url(v)


class RouterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    display_name: str
    api_base_url: str
    api_port: int
    network_role: str
    admin_state: RouterAdminStateEnum
    physical_location: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    online_since_date: date
    serial_number: str
    tags: list[str] = Field(default_factory=list)
    operational_notes: str | None = None
    site_contact_info: str | None = None

    ros_identity: str | None = None
    board_name: str | None = None
    model_name: str | None = None
    architecture_name: str | None = None
    ros_version: str | None = None
    firmware_version: str | None = None

    ssl_trust_status: SSLTrustStatusEnum
    ssl_sha256_fingerprint: str | None = None
    is_reachable: bool = False
    last_seen_at: datetime | None = None
    last_discovery_sync_at: datetime | None = None

    # Métricas y estado efímero enriquecidos desde Redis (Zero-Metrics)
    operational_status: str = "OFFLINE"
    cpu_load_percent: int | None = None
    memory_used_percent: int | None = None

    created_at: datetime
    updated_at: datetime


class RePinSSLRequest(StrictBaseModel):
    totp_code: str = Field(..., min_length=6, max_length=10)
    expected_new_sha256_fingerprint: str = Field(..., min_length=64, max_length=64)


# ============================================================================
# IMPORTACIÓN MASIVA CSV
# ============================================================================


class CsvDryRunRowPreview(BaseModel):
    line: int = 1
    row_number: int = 1
    display_name: str
    ip_address: str = ""
    serial_number: str = ""
    is_valid: bool
    error: str | None = None
    errors: list[str] = Field(default_factory=list)


class CsvDryRunResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    can_proceed: bool
    rows: list[CsvDryRunRowPreview] = Field(default_factory=list)
    rows_preview: list[CsvDryRunRowPreview] = Field(default_factory=list)


class CsvCommitRowItem(StrictBaseModel):
    display_name: str = Field(..., min_length=2, max_length=120)
    api_base_url: str = Field(..., min_length=5, max_length=255)
    api_port: int = Field(default=443, ge=1, le=65535)
    api_username: str = Field(default="rosgrid_api_admin", min_length=1, max_length=64)
    api_password: str = Field(..., min_length=1)
    network_role: str = Field(default="EDGE_BGP", min_length=2, max_length=64)
    admin_state: RouterAdminStateEnum = RouterAdminStateEnum.PRODUCTION
    physical_location: str = Field(..., min_length=2, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    online_since_date: date
    serial_number: str = Field(..., min_length=1, max_length=64)
    tags: list[str] = Field(default_factory=list)
    auto_rotate_credentials: bool = True
    rotation_interval_days: int = Field(default=30, ge=1, le=365)

    @field_validator("api_base_url")
    @classmethod
    def check_api_base_url(cls, v: str) -> str:
        return validate_router_target_url(v) or v


class CsvCommitRequest(StrictBaseModel):
    rows: list[CsvCommitRowItem] = Field(..., min_length=1, max_length=500)


class CsvCommitResponse(BaseModel):
    imported_count: int
    created_router_ids: list[uuid.UUID]


# ============================================================================
# BÓVEDA CRIPTOGRÁFICA Y ROTACIÓN (STEP-UP AUTH)
# ============================================================================


class VaultRevealRequest(StrictBaseModel):
    totp_code: str = Field(..., min_length=6, max_length=10)
    reason: str = Field(..., min_length=5, max_length=255)


class VaultRevealResponse(BaseModel):
    router_id: uuid.UUID
    api_username: str
    current_password: str
    previous_password: str | None = None
    last_rotated_at: datetime
    next_rotation_due_at: datetime | None = None
    display_ttl_seconds: int = 30


class VaultRotateResponse(BaseModel):
    router_id: uuid.UUID
    status: str
    last_rotated_at: datetime


# ============================================================================
# VENTANAS DE MANTENIMIENTO PROGRAMADAS
# ============================================================================


class CreateMaintenanceWindowRequest(StrictBaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    reason: str = Field(..., min_length=5)
    router_id: uuid.UUID | None = None
    target_tag: str | None = Field(default=None, max_length=48)
    starts_at: datetime
    ends_at: datetime
    suppress_alerts: bool = True


class MaintenanceWindowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    reason: str
    router_id: uuid.UUID | None = None
    target_tag: str | None = None
    starts_at: datetime
    ends_at: datetime
    suppress_alerts: bool
    is_cancelled: bool
    created_by: uuid.UUID
    created_at: datetime
