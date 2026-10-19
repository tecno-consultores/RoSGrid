# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para la Suite de Diagnóstico 360° (Hito 18.1)."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class Endpoint360Request(StrictBaseModel):
    """Solicitud de diagnóstico exhaustivo de abonado o enlace."""

    router_id: uuid.UUID = Field(..., description="ID del router MikroTik de acceso")
    target_ip: str = Field(..., min_length=1, max_length=64, description="Dirección IP o prefijo del abonado")
    device_serial: str | None = Field(None, max_length=64, description="Serial físico de la ONU o equipo CPE")
    interface: str | None = Field(None, max_length=64, description="Interfaz o VLAN opcional para muestreo Torch")


class PingMtuStats(BaseModel):
    """Métricas de ping para un tamaño de paquete específico."""

    size: int
    sent: int
    received: int
    packet_loss_pct: float
    min_rtt_ms: float | None = None
    avg_rtt_ms: float | None = None
    max_rtt_ms: float | None = None
    jitter_ms: float | None = None
    df_bit: bool = False


class MultiMtuPingSummary(BaseModel):
    """Resumen de latencia, jitter y dispersión MTU secuencial."""

    ping_64: PingMtuStats
    ping_512: PingMtuStats
    ping_1472: PingMtuStats
    mtu_dispersion_detected: bool = False
    mtu_pass_1500: bool = True


class DisconnectLogItem(BaseModel):
    """Línea relevante de log de desconexión."""

    time: str | None = None
    topics: str | None = None
    message: str


class DisconnectLogAnalysis(BaseModel):
    """Resultado del análisis forense de desconexiones en RouterOS."""

    detected_reason: str = Field(
        ...,
        description="Motivo clasificado: 'user request', 'peer is not responding', 'link down', 'authentication failed', o 'none_detected'",
    )
    last_disconnect_time: str | None = None
    matched_logs: list[DisconnectLogItem] = Field(default_factory=list)


class TorchTopFlowItem(BaseModel):
    """Muestreo de flujo activo de consumo en la interfaz."""

    protocol: str
    port: int | None = None
    src_address: str | None = None
    dst_address: str | None = None
    tx_rate_kbps: float = 0.0
    rx_rate_kbps: float = 0.0


class Endpoint360Response(BaseModel):
    """Respuesta unificada de la Suite de Diagnóstico 360°."""

    router_id: uuid.UUID
    target_ip: str
    device_serial: str | None = None
    interface: str | None = None
    overall_status: str = Field(..., description="OPTIMAL, DEGRADED o DOWN")
    multi_mtu: MultiMtuPingSummary
    disconnect_analysis: DisconnectLogAnalysis
    torch_top_flows: list[TorchTopFlowItem] = Field(default_factory=list)
    diagnostic_timestamp: str
    raw_details: dict[str, Any] = Field(default_factory=dict)
