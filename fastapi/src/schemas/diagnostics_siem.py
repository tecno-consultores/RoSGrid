# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Esquemas Pydantic para Paquete de Diagnóstico 1-Click y Conector SIEM del ISP (Spec 72)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BundleArchiveFormat = Literal["zip", "tar.gz"]
SiemProtocolType = Literal["GELF_UDP", "GELF_HTTP", "SYSLOG_UDP", "SYSLOG_TCP", "LOKI_HTTP"]
SiemLogLevelType = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]


class UiErrorTelemetryItem(BaseModel):
    """Evento individual capturado en el Ring Buffer de diagnóstico del Frontend Vue 3."""

    timestamp: str = Field(..., max_length=64, description="Marca de tiempo ISO-8601 del evento en el navegador.")
    category: Literal["HTTP_ERROR", "VUE_EXCEPTION", "UNHANDLED_REJECTION", "API_LATENCY", "MANUAL_NOTE"] = Field(
        default="HTTP_ERROR",
        description="Categoría del evento de diagnóstico capturado en cliente.",
    )
    message: str = Field(..., max_length=1000, description="Mensaje técnico del error o advertencia.")
    route: str = Field(default="/", max_length=255, description="Ruta activa en Vue Router cuando ocurrió el evento.")
    status_code: int | None = Field(default=None, description="Código HTTP si proviene de una respuesta de API.")
    url: str | None = Field(default=None, max_length=500, description="Endpoint o recurso involucrado.")
    latency_ms: float | None = Field(default=None, description="Latencia observada en milisegundos.")


class UiErrorTelemetryRecordResponse(BaseModel):
    """Respuesta tras registrar un evento de telemetría de error de UI en KeyDB."""

    recorded: bool
    buffered_count: int
    forwarded_to_siem: bool = False


class DiagnosticBundleRequest(BaseModel):
    """Solicitud para generar y descargar el paquete de soporte y diagnóstico sanitizado."""

    model_config = ConfigDict(extra="forbid")

    format: BundleArchiveFormat = Field(
        default="zip",
        description="Formato del archivo comprimido de soporte ('zip' por defecto o 'tar.gz').",
    )
    log_lines_limit: int = Field(
        default=500,
        ge=50,
        le=2000,
        description="Cantidad máxima de líneas recientes de log del backend a incluir.",
    )
    operator_notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Notas opcionales del administrador describiendo el síntoma o incidente.",
    )
    include_frontend_buffer: list[UiErrorTelemetryItem] = Field(
        default_factory=list,
        max_length=200,
        description="Eventos capturados en el Ring Buffer en memoria del navegador.",
    )


class DiagnosticBundleResponse(BaseModel):
    """Respuesta con el archivo comprimido codificado en Base64 listo para descarga directa."""

    filename: str
    format: BundleArchiveFormat
    content_type: str
    size_bytes: int
    redacted_secrets_count: int
    included_files: list[str]
    generated_at: datetime
    bundle_base64: str


class SiemForwarderConfigUpdateRequest(BaseModel):
    """Solicitud para configurar el reenvío de logs hacia el servidor SIEM del ISP."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=False, description="Activa o desactiva el reenvío hacia el SIEM del ISP.")
    protocol: SiemProtocolType = Field(
        default="GELF_UDP",
        description="Protocolo del colector SIEM (GELF_UDP, GELF_HTTP, SYSLOG_UDP, SYSLOG_TCP, LOKI_HTTP).",
    )
    host: str = Field(
        default="127.0.0.1",
        min_length=1,
        max_length=255,
        description="Hostname o IP del servidor Graylog, Loki o Syslog del ISP.",
    )
    port: int = Field(default=12201, ge=1, le=65535, description="Puerto UDP/TCP/HTTP de escucha del SIEM.")
    endpoint_path: str = Field(
        default="/gelf",
        max_length=255,
        description="Ruta HTTP para GELF_HTTP ('/gelf') o LOKI_HTTP ('/loki/api/v1/push').",
    )
    use_tls: bool = Field(default=False, description="Usa HTTPS en protocolos basados en HTTP (GELF_HTTP / LOKI_HTTP).")
    min_level: SiemLogLevelType = Field(
        default="WARNING",
        description="Nivel mínimo de severidad a reenviar al SIEM.",
    )
    include_frontend_errors: bool = Field(
        default=True,
        description="Reenvía también errores reportados por el navegador de los operadores.",
    )
    include_audit_events: bool = Field(
        default=True,
        description="Reenvía eventos administrativos relevantes al SIEM del ISP.",
    )
    custom_stream_label: str = Field(
        default="rosgrid-noc",
        min_length=1,
        max_length=64,
        description="Etiqueta de stream o facility identificadora de esta instancia RoSGrid.",
    )
    auth_token: str | None = Field(
        default=None,
        max_length=512,
        description="Token Bearer opcional para colectores HTTP autenticados (se preserva si se envía vacío).",
    )


class SiemForwarderConfigResponse(BaseModel):
    """Estado de configuración actual del conector SIEM del ISP (sin exponer secretos)."""

    enabled: bool
    protocol: SiemProtocolType
    host: str
    port: int
    endpoint_path: str
    use_tls: bool
    min_level: SiemLogLevelType
    include_frontend_errors: bool
    include_audit_events: bool
    custom_stream_label: str
    has_auth_token: bool
    updated_at: str | None = None


class SiemTestDeliveryResponse(BaseModel):
    """Resultado de la prueba de conectividad y envío hacia el SIEM del ISP."""

    success: bool
    protocol: SiemProtocolType
    target: str
    latency_ms: float
    detail: str


class VersionCheckStatusResponse(BaseModel):
    """Estado del comprobador pasivo de nuevas versiones en GitHub Releases (Zero Auto-Update)."""

    enabled: bool
    current_version: str
    latest_version: str | None = None
    update_available: bool = False
    release_url: str
    release_name: str | None = None
    published_at: str | None = None
    last_checked_at: str | None = None
    last_status: str = "pending"
