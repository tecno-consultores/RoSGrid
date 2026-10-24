# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CveSeverity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


class CveItem(BaseModel):
    cve_id: str = Field(..., description="Identificador CVE oficial (ej. CVE-2023-32154)")
    title: str = Field(..., description="Título descriptivo en español")
    cvss_score: float = Field(..., ge=0.0, le=10.0, description="Puntuación CVSS v3")
    severity: CveSeverity = Field(..., description="Nivel de severidad según CVSS")
    affected_versions_expr: str = Field(..., description="Expresión de versiones afectadas (ej. >=7.0.0,<7.9.2)")
    fixed_in_version: str = Field(..., description="Versión mínima donde se subsana la vulnerabilidad")
    description_es: str = Field(..., description="Descripción técnica en español")
    remediation: str = Field(..., description="Recomendación técnica y acciones de mitigación")
    published_date: str = Field(..., description="Fecha de publicación del boletín")


class RouterCveEvaluation(BaseModel):
    router_id: uuid.UUID
    display_name: str
    ros_version: str | None
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    max_cvss_score: float
    vulnerabilities: list[CveItem]
    recommended_target_version: str | None = Field(
        None, description="Versión sugerida para resolver todas las vulnerabilidades detectadas"
    )


class FleetCveSummary(BaseModel):
    total_evaluated_routers: int
    vulnerable_routers_count: int
    critical_routers_count: int
    high_routers_count: int
    total_unique_cves: int
    summary_by_severity: dict[str, int]
    vulnerable_routers: list[RouterCveEvaluation]
    timestamp: datetime
    last_synced_at: datetime | None = Field(
        None, description="Timestamp UTC de la última sincronización de boletines remotos"
    )
    cache_expires_at: datetime | None = Field(
        None, description="Timestamp UTC en que expira la validez del caché de 24 horas"
    )
    cache_ttl_seconds: int | None = Field(
        None, description="Segundos restantes de validez del caché en KeyDB"
    )
    is_cache_fresh: bool = Field(
        True, description="Indica si el catálogo en caché se encuentra vigente (< 24 horas)"
    )
    auto_synced: bool = Field(
        False, description="Indica si se ejecutó una sincronización automática al ingresar por primera vez en el día"
    )


class CveSyncResponse(BaseModel):
    success: bool
    source_url: str
    total_cves: int
    updated_at: datetime
    message: str
