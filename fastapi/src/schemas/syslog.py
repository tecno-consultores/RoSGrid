# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SyslogEvent(BaseModel):
    timestamp: datetime = Field(..., description="Marca de tiempo del evento")
    facility: str = Field("daemon", description="Facility Syslog (ej. daemon, local0)")
    severity: str = Field("info", description="Nivel de severidad (critical, error, warning, info)")
    topics: str = Field("", description="Tópicos de RouterOS (ej. interface,warning o route,bgp)")
    message: str = Field(..., description="Cuerpo del mensaje")
    is_critical: bool = Field(False, description="True si coincide con un patrón crítico evaluado en vuelo")
    raw: str = Field(..., description="Línea cruda recibida en el socket")


class RouterSyslogResponse(BaseModel):
    router_id: uuid.UUID
    total_in_buffer: int = Field(0, description="Cantidad total de eventos en el RingBuffer")
    total_events: int = Field(0, description="Alias para paridad de contrato con frontend")
    critical_count: int = Field(0, description="Cantidad de eventos críticos en el buffer")
    events: list[SyslogEvent] = Field(default_factory=list)


class SyslogTemplateResponse(BaseModel):
    template_content: str
    default_port: int
    protocol: str = Field("UDP", description="Protocolo de transporte")
    instructions: str = Field("", description="Instrucciones en inglés")
    instructions_es: str = Field("", description="Instrucciones en español")
