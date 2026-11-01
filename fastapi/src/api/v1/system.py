# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Diagnóstico del Sistema y Telemetría Anónima de Instancias Activas (Spec 55 / Hito 27.18)."""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from src.api.deps import require_roles
from src.models.core import SystemRoleEnum
from src.workers.telemetry_beacon_worker import (
    get_telemetry_beacon_status,
    send_telemetry_heartbeat_once,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System Management & Telemetry"])

_SYSTEM_ADMIN_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
)


@router.get(
    "/telemetry-beacon/status",
    summary="Estado de Telemetría Anónima de Instancias Activas",
    description="Retorna el estado del latido Zero-PII, identificador anónimo irreversible y último envío.",
    dependencies=[Depends(require_roles(*_SYSTEM_ADMIN_ROLES))],
)
async def get_beacon_status() -> dict[str, Any]:
    """Consulta el estado del latido de telemetría anónima de la instalación (CC = 1)."""
    return await get_telemetry_beacon_status()


@router.post(
    "/telemetry-beacon/trigger",
    summary="Disparo Manual de Latido de Telemetría",
    description="Fuerza un envío inmediato fail-silent del latido anónimo hacia rosgrid-web.",
    dependencies=[Depends(require_roles(*_SYSTEM_ADMIN_ROLES))],
)
async def trigger_beacon_now() -> dict[str, Any]:
    """Ejecuta de forma inmediata un latido anónimo de telemetría hacia el portal oficial (CC = 1)."""
    return await send_telemetry_heartbeat_once()
