# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Endpoints de Diagnóstico del Sistema y Telemetría Anónima de Instancias Activas (Spec 55 / Hito 27.18 y Spec 72 / Hito 29)."""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user_claims, require_roles
from src.models.core import SystemRoleEnum
from src.schemas.diagnostics_siem import (
    DiagnosticBundleRequest,
    DiagnosticBundleResponse,
    SiemForwarderConfigResponse,
    SiemForwarderConfigUpdateRequest,
    SiemTestDeliveryResponse,
    UiErrorTelemetryItem,
    UiErrorTelemetryRecordResponse,
)
from src.services.diagnostics_and_siem import (
    build_support_bundle_archive,
    get_siem_forwarder_config,
    record_ui_error_telemetry,
    send_siem_test_event,
    update_siem_forwarder_config,
)
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


def _resolve_tenant_key(claims: dict[str, Any]) -> str:
    """Resuelve el identificador de tenant para aislar buffers de diagnóstico y SIEM en KeyDB (CC = 1)."""
    return str(claims.get("tid") or "global")


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


@router.post(
    "/diagnostics/ui-error",
    response_model=UiErrorTelemetryRecordResponse,
    summary="Registrar Evento de Telemetría de Error de UI (Multi-Operador L1/L2/L3/Admin)",
    description="Permite a cualquier operador autenticado del tenant reportar fallas de UI/HTTP al Ring Buffer compartido en KeyDB y al SIEM del ISP.",
)
async def report_ui_error_telemetry(
    payload: UiErrorTelemetryItem,
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> UiErrorTelemetryRecordResponse:
    """Registra un evento del Ring Buffer del navegador en KeyDB con trazabilidad de usuario y rol (CC = 1)."""
    role_val = str(claims.get("rol") or "UNKNOWN")
    username_val = str(claims.get("usr") or claims.get("username") or "operator")
    return await record_ui_error_telemetry(
        _resolve_tenant_key(claims),
        payload,
        reported_by_username=username_val,
        reported_by_role=role_val,
    )


@router.post(
    "/diagnostics/bundle",
    response_model=DiagnosticBundleResponse,
    summary="Generar Paquete de Diagnóstico 1-Click (.zip / .tar.gz)",
    description="Genera un paquete comprimido sanitizado con logs de frontend, backend y estado del sistema.",
    dependencies=[Depends(require_roles(*_SYSTEM_ADMIN_ROLES))],
)
async def create_diagnostic_support_bundle(
    payload: DiagnosticBundleRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> DiagnosticBundleResponse:
    """Construye el archivo .zip o .tar.gz de soporte técnico sin secretos (CC = 1)."""
    role_val = str(claims.get("rol") or "UNKNOWN")
    return await build_support_bundle_archive(_resolve_tenant_key(claims), role_val, payload)


@router.get(
    "/siem-config",
    response_model=SiemForwarderConfigResponse,
    summary="Consultar Configuración del Conector SIEM del ISP",
    description="Retorna la configuración de reenvío hacia Graylog, Grafana Loki o Syslog del ISP.",
    dependencies=[Depends(require_roles(*_SYSTEM_ADMIN_ROLES))],
)
async def read_isp_siem_config(
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> SiemForwarderConfigResponse:
    """Consulta la configuración SIEM del tenant actual (CC = 1)."""
    return await get_siem_forwarder_config(_resolve_tenant_key(claims))


@router.put(
    "/siem-config",
    response_model=SiemForwarderConfigResponse,
    summary="Actualizar Configuración del Conector SIEM del ISP",
    description="Actualiza protocolo (GELF/Loki/Syslog), host, puerto y filtros de severidad del SIEM del ISP.",
    dependencies=[Depends(require_roles(*_SYSTEM_ADMIN_ROLES))],
)
async def save_isp_siem_config(
    payload: SiemForwarderConfigUpdateRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> SiemForwarderConfigResponse:
    """Actualiza la configuración SIEM del tenant actual en KeyDB (CC = 1)."""
    return await update_siem_forwarder_config(_resolve_tenant_key(claims), payload)


@router.post(
    "/siem-config/test",
    response_model=SiemTestDeliveryResponse,
    summary="Enviar Log de Prueba al Colector SIEM del ISP",
    description="Envía un mensaje de prueba hacia el servidor Graylog, Loki o Syslog configurado y retorna latencia.",
    dependencies=[Depends(require_roles(*_SYSTEM_ADMIN_ROLES))],
)
async def test_isp_siem_delivery(
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> SiemTestDeliveryResponse:
    """Ejecuta la prueba de entrega hacia el colector SIEM del ISP (CC = 1)."""
    return await send_siem_test_event(_resolve_tenant_key(claims))
