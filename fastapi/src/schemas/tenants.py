# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from src.models.core import TenantStatusEnum

# Valores por defecto oficiales de los Feature Flags (specs/34 §1).
TENANT_FEATURE_DEFAULTS: dict[str, Any] = {
    "isp_module_enabled": True,
    "bgp_looking_glass_enabled": False,
    "sfp_ddm_telemetry_enabled": True,
    "ipfix_analytics_enabled": False,
    "enforce_maker_checker": True,
    "auto_safemode_enforced": True,
    "ai_mcp_integration_enabled": True,
    "nightly_backups_enabled": True,
    "outbound_webhooks_enabled": True,
    "config_drift_monitoring_enabled": False,
    "cis_audit_enabled": True,
    "sdwan_orchestrator_enabled": False,
    "capsman_wifi_enabled": False,
    "sla_tracker_enabled": False,
    "mass_outage_threshold": 10,
    "default_locale": "es",
    "l2_topology_enabled": True,
    "syslog_collector_enabled": True,
    "cve_scanner_enabled": True,
    "prometheus_fleet_exporter_enabled": True,
}

SUPPORTED_LOCALES_PATTERN = r"^(es|en)$"


def extract_tenant_features(tenant: Any) -> dict[str, Any]:
    """Extrae los Feature Flags de un objeto Tenant aplicando los valores por defecto ante nulos."""
    features: dict[str, Any] = {}
    for key, default in TENANT_FEATURE_DEFAULTS.items():
        value = getattr(tenant, key, None)
        features[key] = default if value is None else value
    return features


class CreateTenantRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(..., min_length=2, max_length=150)
    tax_id: str | None = Field(None, max_length=64)
    max_routers_quota: int = Field(100, gt=0)
    max_users_quota: int = Field(50, gt=0)
    require_2fa_all_users: bool = True
    default_safemode_seconds: int = Field(60, ge=15, le=300)

    # Administrador inicial del tenant
    admin_username: str = Field(..., min_length=3, max_length=64)
    admin_email: EmailStr
    admin_full_name: str = Field(..., min_length=3, max_length=150)
    admin_password: str = Field(..., min_length=8)


class UpdateTenantFeaturesRequest(BaseModel):
    """Cuerpo PATCH de `/tenants/{id}/features` (Panel "Módulos & Capacidades")."""

    model_config = ConfigDict(extra="forbid")

    isp_module_enabled: bool | None = None
    bgp_looking_glass_enabled: bool | None = None
    sfp_ddm_telemetry_enabled: bool | None = None
    ipfix_analytics_enabled: bool | None = None
    enforce_maker_checker: bool | None = None
    auto_safemode_enforced: bool | None = None
    ai_mcp_integration_enabled: bool | None = None
    nightly_backups_enabled: bool | None = None
    outbound_webhooks_enabled: bool | None = None
    config_drift_monitoring_enabled: bool | None = None
    cis_audit_enabled: bool | None = None
    sdwan_orchestrator_enabled: bool | None = None
    capsman_wifi_enabled: bool | None = None
    sla_tracker_enabled: bool | None = None
    mass_outage_threshold: int | None = Field(None, ge=1, le=1000)
    default_locale: str | None = Field(None, pattern=SUPPORTED_LOCALES_PATTERN)
    l2_topology_enabled: bool | None = None
    syslog_collector_enabled: bool | None = None
    cve_scanner_enabled: bool | None = None
    prometheus_fleet_exporter_enabled: bool | None = None


class UpdateTenantRequest(UpdateTenantFeaturesRequest):
    name: str | None = Field(None, min_length=2, max_length=150)
    tax_id: str | None = None
    status: TenantStatusEnum | None = None
    max_routers_quota: int | None = Field(None, gt=0)
    max_users_quota: int | None = Field(None, gt=0)
    require_2fa_all_users: bool | None = None
    default_safemode_seconds: int | None = Field(None, ge=15, le=300)


class TenantFeatureFlagsMixin(BaseModel):
    """Bloque común de Feature Flags con relleno automático de valores por defecto."""

    model_config = ConfigDict(from_attributes=True)

    isp_module_enabled: bool = True
    bgp_looking_glass_enabled: bool = False
    sfp_ddm_telemetry_enabled: bool = True
    ipfix_analytics_enabled: bool = False
    enforce_maker_checker: bool = True
    auto_safemode_enforced: bool = True
    ai_mcp_integration_enabled: bool = True
    nightly_backups_enabled: bool = True
    outbound_webhooks_enabled: bool = True
    config_drift_monitoring_enabled: bool = False
    cis_audit_enabled: bool = True
    sdwan_orchestrator_enabled: bool = False
    capsman_wifi_enabled: bool = False
    sla_tracker_enabled: bool = False
    mass_outage_threshold: int = 10
    default_locale: str = "es"
    l2_topology_enabled: bool = True
    syslog_collector_enabled: bool = True
    cve_scanner_enabled: bool = True
    prometheus_fleet_exporter_enabled: bool = True

    @model_validator(mode="before")
    @classmethod
    def fill_missing_feature_defaults(cls, data: Any) -> Any:
        source = data if isinstance(data, dict) else {name: getattr(data, name, None) for name in cls.model_fields}
        merged = dict(source)
        for key, default in TENANT_FEATURE_DEFAULTS.items():
            if merged.get(key) is None:
                merged[key] = default
        return merged


class TenantFeaturesResponse(TenantFeatureFlagsMixin):
    pass


class TenantResponse(TenantFeatureFlagsMixin):
    id: uuid.UUID
    slug: str
    name: str
    tax_id: str | None
    status: TenantStatusEnum
    max_routers_quota: int
    max_users_quota: int
    require_2fa_all_users: bool
    default_safemode_seconds: int
    created_at: datetime
    updated_at: datetime
