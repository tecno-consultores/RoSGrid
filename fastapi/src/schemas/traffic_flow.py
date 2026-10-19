# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para Detección de Tráfico Anómalo y Mitigación Rápida (Hito 18.3)."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


class TrafficAnomalyItem(BaseModel):
    """Detalle de una dirección IP con comportamiento o tasa anómala."""

    ip_address: str
    connection_count: int
    estimated_pps: int
    protocols: list[str] = Field(default_factory=list)
    anomaly_type: str = Field(
        ...,
        description="Tipo de anomalía detectada: HIGH_CONNECTION_COUNT, HIGH_PPS_BURST o POSSIBLE_SYN_FLOOD",
    )
    severity: str = Field(..., description="Nivel de criticidad: WARNING, HIGH o CRITICAL")


class TrafficAnomaliesResponse(BaseModel):
    """Resultado del escaneo de anomalías de flujo y conexiones en el router."""

    router_id: uuid.UUID
    threshold_pps: int
    threshold_conns: int
    anomalies_detected: int
    items: list[TrafficAnomalyItem] = Field(default_factory=list)


class TrafficMitigationRequest(StrictBaseModel):
    """Solicitud de mitigación inmediata ante tráfico malicioso o abusivo."""

    router_id: uuid.UUID = Field(..., description="ID del router donde aplicar la mitigación")
    target_ip: str = Field(..., min_length=1, max_length=64, description="Dirección IP anómala a aislar")
    action: Literal["fast_drop", "blackhole"] = Field(
        default="fast_drop",
        description="Estrategia: fast_drop (filtro RAW/Address-List) o blackhole (ruta nula)",
    )
    comment: str = Field(
        default="RoSGrid Anomaly FastDrop Mitigation",
        max_length=128,
        description="Comentario descriptivo para la regla o ruta",
    )
    duration_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Tiempo de permanencia del aislamiento en segundos (por defecto 1h)",
    )


class TrafficMitigationResponse(BaseModel):
    """Confirmación de mitigación aplicada bajo Safe Mode."""

    status: str
    router_id: uuid.UUID
    target_ip: str
    action_taken: str
    rule_or_list_id: str
    safemode_applied: bool = True
    audit_event: str = "TRAFFIC_ANOMALY_MITIGATED"
