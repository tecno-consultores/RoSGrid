# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic para el Aprovisionamiento Técnico de Servicios de Red."""

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChangeRateLimitRequest(BaseModel):
    """Solicitud de modificación de perfil de ancho de banda / QoS en caliente."""

    bandwidth_profile_id: uuid.UUID = Field(
        ..., description="UUID del perfil de ancho de banda destino a aplicar en MikroTik"
    )


class NetworkServiceActionResponse(BaseModel):
    """Respuesta unificada de aprovisionamiento técnico e idempotencia."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(
        ...,
        description="Estado de la operación: ISOLATED, ALREADY_ISOLATED, RESTORED, ALREADY_ACTIVE, RATE_LIMIT_UPDATED",
    )
    service_id: uuid.UUID = Field(..., description="UUID del servicio o equipo de abonado")
    endpoint_identifier: Optional[str] = Field(
        None, description="Identificador técnico (usuario PPPoE o ID de circuito)"
    )
    message: str = Field(..., description="Mensaje explicativo del estado resultante")
    bandwidth_profile_id: Optional[uuid.UUID] = Field(None, description="UUID del perfil de ancho de banda actual")
    bandwidth_profile_name: Optional[str] = Field(None, description="Nombre descriptivo del perfil de ancho de banda")
    rate_down_kbps: Optional[int] = Field(None, description="Tasa nominal de bajada en kbps")
    rate_up_kbps: Optional[int] = Field(None, description="Tasa nominal de subida en kbps")


class NetworkServiceDetailResponse(BaseModel):
    """Detalle completo del estado técnico de un servicio de red."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID
    device_serial: Optional[str] = None
    endpoint_identifier: Optional[str] = None
    assigned_ipv4: Optional[str] = None
    assigned_ipv6_prefix: Optional[str] = None
    bandwidth_profile_id: Optional[uuid.UUID] = None
    onu_mode: str
    status: str
    last_reachability_status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
