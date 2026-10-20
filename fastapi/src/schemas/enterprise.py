# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para la Suite Corporativa (Hito 20 / specs/33).

Cubre: Config Drift, SD-WAN WireGuard Hub & Spoke, CIS Benchmark Hardening,
Switching & Rogue DHCP, SLA Tracker y WiFi CAPsMAN / WiFiWave2.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 1. Config Drift & Golden Templates (Sub-tarea 20.1)
# ============================================================================


class GoldenTemplateCreateRequest(StrictBaseModel):
    """Solicitud para dar de alta una plantilla de configuración homologada."""

    name: str = Field(..., min_length=2, max_length=120)
    network_role: str = Field("BRANCH", max_length=64, description="BRANCH, EDGE, CORE, CAMPUS")
    baseline_rsc_content: str = Field(..., min_length=5, description="Contenido de script canónico RouterOS")
    enforce_strict_firewall: bool = Field(True)
    enforce_ntp_dns: bool = Field(True)


class GoldenTemplateResponse(BaseModel):
    """Representación de una plantilla de configuración homologada."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    network_role: str
    baseline_rsc_content: str
    enforce_strict_firewall: bool
    enforce_ntp_dns: bool
    created_at: datetime
    updated_at: datetime


class ConfigDriftCheckResponse(BaseModel):
    """Resultado del análisis de desviación respecto a la Golden Template."""

    router_id: uuid.UUID
    router_name: str
    network_role: str
    drift_detected: bool
    baseline_template_name: str
    added_lines: list[str]
    removed_lines: list[str]
    diff_unified: str
    total_drift_lines: int
    checked_at: str


class ConfigDriftRevertRequest(StrictBaseModel):
    """Solicitud de reversión en 1 clic hacia la configuración homologada."""

    router_id: uuid.UUID
    template_id: uuid.UUID | None = None
    reason: str | None = Field(None, max_length=255)


class ConfigDriftRevertResponse(BaseModel):
    """Resultado de la remediación de drift con Safe Mode y auditoría WORM."""

    router_id: uuid.UUID
    status: str
    executed_safemode: bool
    audit_log_id: str
    remediation_summary: str


# ============================================================================
# 2. SD-WAN WireGuard Hub & Spoke (Sub-tarea 20.2)
# ============================================================================


class SdwanProvisionSpokeRequest(StrictBaseModel):
    """Parámetros de aprovisionamiento Zero-Touch de sucursal Spoke."""

    hub_router_id: uuid.UUID
    spoke_router_id: uuid.UUID
    spoke_name: str = Field(..., min_length=2, max_length=120)
    allocated_subnet: str | None = Field(None, max_length=64, description="Ej. 10.250.0.0/31 o /30")
    hub_endpoint: str | None = Field(None, max_length=128, description="IP o FQDN con puerto del Hub")
    spoke_public_key: str | None = Field(None, max_length=128)
    routing_protocol: str = Field("OSPF", max_length=32, description="OSPF o BGP")
    multi_wan_failover_enabled: bool = Field(True)


class SdwanSpokeTunnelResponse(BaseModel):
    """Detalle de un túnel Spoke aprovisionado en la malla SD-WAN."""

    id: uuid.UUID
    hub_router_id: uuid.UUID
    spoke_router_id: uuid.UUID
    spoke_name: str
    interface_name: str
    allocated_subnet: str
    hub_endpoint: str
    spoke_public_key: str
    routing_protocol: str
    multi_wan_failover_enabled: bool
    status: str
    rx_bytes: int = 0
    tx_bytes: int = 0
    latency_ms: float = 0.0
    created_at: datetime


class SdwanTopologyResponse(BaseModel):
    """Topología completa de la malla SD-WAN del tenant."""

    tenant_id: uuid.UUID
    total_spokes: int
    active_spokes: int
    degraded_spokes: int
    down_spokes: int
    tunnels: list[SdwanSpokeTunnelResponse]


class SdwanMultiWanFailoverRequest(StrictBaseModel):
    """Configuración de failover inteligente multi-WAN con PBR y Netwatch."""

    router_id: uuid.UUID
    primary_wan_interface: str = Field("ether1", max_length=64)
    backup_wan_interface: str = Field("lte1", max_length=64)
    check_host: str = Field("1.1.1.1", max_length=64)
    failover_threshold_ms: float = Field(150.0)


class SdwanMultiWanFailoverResponse(BaseModel):
    """Resultado del despliegue de rutas recursivas y Netwatch."""

    router_id: uuid.UUID
    failover_policy_deployed: bool
    netwatch_script_id: str
    deployed_under_safemode: bool


# ============================================================================
# 3. Auditoría de Seguridad & Endurecimiento CIS Benchmark (Sub-tarea 20.3)
# ============================================================================


class CisDirectiveResult(BaseModel):
    """Resultado individual de una de las 10 directivas críticas CIS."""

    code: str
    title: str
    passed: bool
    weight: int
    finding: str
    remediation_cmd: str


class CisAuditResponse(BaseModel):
    """Resultado global del escaneo de seguridad CIS Benchmark RouterOS."""

    router_id: uuid.UUID
    router_name: str
    security_score: int
    compliance_grade: str
    total_directives: int
    passed_directives: int
    failed_directives: int
    directives: list[CisDirectiveResult]
    audited_at: str


class CisAutoHardenRequest(StrictBaseModel):
    """Solicitud de endurecimiento automático (Auto-Hardening)."""

    router_id: uuid.UUID
    directive_codes_to_apply: list[str] | None = None


class CisAutoHardenResponse(BaseModel):
    """Resultado del endurecimiento aplicado con Safe Mode."""

    router_id: uuid.UUID
    new_security_score: int
    applied_directives_count: int
    executed_under_safemode: bool
    remediation_script: str
    audit_log_id: str


# ============================================================================
# 4. Switching & Detección de Rogue DHCP (Sub-tarea 20.4)
# ============================================================================


class DhcpSnoopingState(BaseModel):
    """Estado de DHCP Snooping en un bridge específico."""

    bridge_name: str
    dhcp_snooping_enabled: bool
    trusted_ports: list[str]
    untrusted_ports: list[str]


class DhcpSnoopingEnableRequest(StrictBaseModel):
    """Solicitud para habilitar DHCP Snooping y marcar puertos troncales/acceso."""

    router_id: uuid.UUID
    bridge_name: str = Field("bridge", max_length=64)
    trusted_ports: list[str] = Field(default_factory=list)


class RogueDhcpAlertItem(BaseModel):
    """Alerta de servidor DHCP no autorizado detectado en la LAN."""

    id: str
    router_id: uuid.UUID
    bridge_name: str
    interface_name: str
    rogue_server_mac: str
    rogue_server_ip: str | None
    detected_at: str
    status: str


class RogueDhcpIsolatePortRequest(StrictBaseModel):
    """Deshabilitación preventiva de puerto afectado por Rogue DHCP."""

    router_id: uuid.UUID
    interface_name: str = Field(..., max_length=64)
    reason: str | None = Field(None, max_length=255)


class RogueDhcpIsolatePortResponse(BaseModel):
    """Resultado del aislamiento de puerto."""

    router_id: uuid.UUID
    interface_name: str
    isolated: bool
    executed_under_safemode: bool
    audit_log_id: str


# ============================================================================
# 5. Monitor de Cumplimiento de SLA para Enlaces Dedicados (Sub-tarea 20.5)
# ============================================================================


class SlaMetricItem(BaseModel):
    """Métricas continuas de SLA para un enlace o gateway de carrier."""

    id: uuid.UUID
    router_id: uuid.UUID
    target_host: str
    target_name: str
    uptime_percent: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    sla_threshold_ms: float
    compliance_status: str
    recorded_at: datetime


class SlaProbeRunRequest(StrictBaseModel):
    """Ejecución de ciclo de sondeo de prueba SLA."""

    router_id: uuid.UUID
    target_host: str = Field(..., min_length=1, max_length=128)
    target_name: str | None = Field("Carrier Primary Gateway", max_length=120)
    count: int | None = Field(20, ge=5, le=100)
    sla_threshold_ms: float | None = Field(50.0, ge=1.0)


class SlaReportSummary(BaseModel):
    """Reporte formal de cumplimiento de SLA para auditoría o penalización."""

    tenant_name: str
    period: str
    total_targets_monitored: int
    global_uptime_percent: float
    total_contract_breaches: int
    total_downtime_minutes: float
    metrics: list[SlaMetricItem]
    exported_at: str


# ============================================================================
# 6. Gestión Centralizada de WiFi Corporativo / CAPsMAN (Sub-tarea 20.6)
# ============================================================================


class CapsmanOverviewResponse(BaseModel):
    """Resumen operativo del controlador CAPsMAN / WiFiWave2."""

    router_id: uuid.UUID
    capsman_running: bool
    active_radios_count: int
    managed_aps_count: int
    connected_clients_count: int


class WifiSsidProfile(BaseModel):
    """Perfil de SSID inalámbrico corporativo."""

    id: str
    name: str
    ssid: str
    security_type: str
    vlan_id: int | None = None
    client_isolation: bool = False
    rate_limit_profile: str | None = None


class WifiClientItem(BaseModel):
    """Cliente inalámbrico conectado a la flota de Access Points."""

    mac_address: str
    ip_address: str | None = None
    hostname: str | None = None
    ap_name: str
    ssid: str
    signal_rssi_dbm: int
    snr_db: int
    wifi_standard: str
    tx_rate_mbps: float
    rx_rate_mbps: float
    fast_roaming_supported: bool
    connected_duration_seconds: int
