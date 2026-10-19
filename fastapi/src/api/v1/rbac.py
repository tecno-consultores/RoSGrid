# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de gestión de Roles, Perfiles y Matriz de Políticas RBAC."""

import json
import logging
import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_roles
from src.db.session import get_db_session, set_tenant_context
from src.models.core import SystemRoleEnum
from src.rbac.policy_matrix import ALLOW, DENY, MAKER_CHECKER, POLICY_MATRIX, READ_ONLY
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rbac", tags=["RBAC Policies & Roles"])

ROLE_METADATA: dict[SystemRoleEnum, dict[str, Any]] = {
    SystemRoleEnum.SUPERADMIN_GLOBAL: {
        "title": "Superadministrador Global",
        "description": "Control absoluto e irrestricto de la plataforma multitenant, administración de empresas, auditoría WORM forense y configuración de infraestructura central.",
        "level": 0,
        "is_system_reserved": True,
        "badge_color": "purple",
    },
    SystemRoleEnum.TENANT_ADMIN: {
        "title": "Administrador de Organización",
        "description": "Máxima autoridad dentro de la empresa o tenant. Gestiona operadores, asigna routers, aprueba cambios Maker-Checker, descarga respaldos y configura redes.",
        "level": 1,
        "is_system_reserved": False,
        "badge_color": "cyan",
    },
    SystemRoleEnum.SUPERVISOR: {
        "title": "Supervisor de Operaciones NOC",
        "description": "Supervisión técnica de cuadrillas. Aprueba cambios Maker-Checker, visualiza auditorías, programa mantenimientos y aprueba operaciones de Soporte L1/L2.",
        "level": 2,
        "is_system_reserved": False,
        "badge_color": "emerald",
    },
    SystemRoleEnum.SUPPORT_L3: {
        "title": "Soporte Técnico Nivel 3 (Senior)",
        "description": "Ingeniería de red avanzada. Ejecuta diagnósticos profundos, modifica configuraciones L1/L2, despliega túneles VPN, enrutamiento BGP/OSPF y aprueba cambios técnicos.",
        "level": 3,
        "is_system_reserved": False,
        "badge_color": "blue",
    },
    SystemRoleEnum.SUPPORT_L2: {
        "title": "Soporte Técnico Nivel 2",
        "description": "Operador de segundo nivel. Gestiona interfaces, diagnostica enlaces en vivo (Ping/Torch/Logs) y reinicia sesiones PPPoE. Cambios críticos pasan por Maker-Checker.",
        "level": 4,
        "is_system_reserved": False,
        "badge_color": "amber",
    },
    SystemRoleEnum.SUPPORT_L1: {
        "title": "Soporte Técnico Nivel 1 (Helpdesk)",
        "description": "Atención primaria a clientes e incidencias. Monitorea estado de routers, visualiza sesiones activas y ejecuta diagnósticos básicos sin modificar configuración directamente.",
        "level": 5,
        "is_system_reserved": False,
        "badge_color": "slate",
    },
    SystemRoleEnum.FIELD_TECH: {
        "title": "Técnico de Campo (Terreno)",
        "description": "Personal técnico en sitio. Diagnostica puertos físicos, prueba transceptores ópticos SFP DDM y cableado TDR para validar conectividad en torres y racks.",
        "level": 6,
        "is_system_reserved": False,
        "badge_color": "orange",
    },
    SystemRoleEnum.INVENTORY_MANAGER: {
        "title": "Gestor de Inventario y Activos",
        "description": "Responsable de hardware MikroTik. Da de alta routers, realiza importaciones masivas por CSV, programa ventanas de mantenimiento y rota credenciales en bóveda.",
        "level": 7,
        "is_system_reserved": False,
        "badge_color": "teal",
    },
    SystemRoleEnum.AUDITOR: {
        "title": "Auditor de Seguridad y Cumplimiento",
        "description": "Auditoría forense de solo lectura estricta. Inspecciona la cadena inmutable WORM SHA-256, revisa logs de acceso y exporta informes certificados sin alterar nada.",
        "level": 8,
        "is_system_reserved": False,
        "badge_color": "indigo",
    },
    SystemRoleEnum.NOC_MONITOR: {
        "title": "Operador de Monitoreo NOC 24/7",
        "description": "Vigilancia continua del estado de red. Visualiza Wallboard, mapas de topología OSM, métricas de telemetría y alarmas sin permisos de escritura ni cambios.",
        "level": 9,
        "is_system_reserved": False,
        "badge_color": "sky",
    },
    SystemRoleEnum.SERVICE_ACCOUNT: {
        "title": "Cuenta de Servicio / API / Agentes IA",
        "description": "Identidad para integraciones automatizadas, agentes IA MCP, sondas externas y recolección de telemetría con permisos específicos de ejecución.",
        "level": 10,
        "is_system_reserved": False,
        "badge_color": "violet",
    },
}

ACTIONS_METADATA: list[dict[str, Any]] = [
    {
        "key": "TENANT_MANAGEMENT",
        "label": "Administración de Empresas (Multi-Tenant)",
        "category": "Administración y Seguridad",
        "description": "Creación, suspensión y cuotas de organizaciones/tenants en RoSGrid.",
    },
    {
        "key": "USER_MANAGEMENT",
        "label": "Gestión de Operadores y Usuarios",
        "category": "Administración y Seguridad",
        "description": "Creación, edición, reseteo 2FA y asignación de roles a operadores.",
    },
    {
        "key": "VIEW_ACTIVE_SESSIONS_KILLSWITCH",
        "label": "Sesiones Activas y Kill-Switch",
        "category": "Administración y Seguridad",
        "description": "Inspección de sesiones concurrentes y desconexión inmediata de tokens.",
    },
    {
        "key": "ROUTER_INVENTORY_CSV",
        "label": "Inventario de Routers y Carga CSV",
        "category": "Operaciones e Inventario",
        "description": "Alta de equipos MikroTik, geolocalización y procesamiento masivo CSV.",
    },
    {
        "key": "REVEAL_VAULT_KEYS",
        "label": "Revelar Credenciales en Bóveda",
        "category": "Administración y Seguridad",
        "description": "Visualización protegida con Step-Up Auth 2FA y autodestrucción en 30s.",
    },
    {
        "key": "TRIGGER_PASSWORD_ROTATION",
        "label": "Rotación de Contraseñas de Equipos",
        "category": "Administración y Seguridad",
        "description": "Disparo manual o programado de rotación criptográfica en MikroTik.",
    },
    {
        "key": "SCHEDULE_MAINTENANCE",
        "label": "Ventanas de Mantenimiento",
        "category": "Operaciones e Inventario",
        "description": "Silenciamiento temporal de alertas y programación de paradas técnicas.",
    },
    {
        "key": "VIEW_OSM_MAP_NOC_CHARTS",
        "label": "Mapas Topológicos OSM y Gráficas NOC",
        "category": "Telemetría y Diagnóstico",
        "description": "Visualización geográfica y telemetría de tráfico en tiempo real.",
    },
    {
        "key": "LIVE_DIAGNOSTICS",
        "label": "Herramientas en Vivo (Ping, Torch, Traceroute)",
        "category": "Telemetría y Diagnóstico",
        "description": "Pruebas de conectividad y análisis de flujos por socket en vivo.",
    },
    {
        "key": "L1_OPERATIONS",
        "label": "Operación de Interfaces y SFP DDM",
        "category": "Configuración y Control de Red",
        "description": "Habilitación/deshabilitación de puertos y diagnóstico óptico láser.",
    },
    {
        "key": "CONFIG_STANDARD_L1",
        "label": "Configuración Estándar Capa 1",
        "category": "Configuración y Control de Red",
        "description": "Parámetros de MTU, comentarios y asignaciones de red estándar.",
    },
    {
        "key": "CRITICAL_NETWORK_ACTIONS",
        "label": "Acciones Críticas de Red (Rutas / BGP)",
        "category": "Configuración y Control de Red",
        "description": "Modificación de tablas de enrutamiento dinámico, filtros y NAT crítico.",
    },
    {
        "key": "REBOOT_SHUTDOWN",
        "label": "Reinicio y Apagado de Routers",
        "category": "Configuración y Control de Red",
        "description": "Reinicio en caliente de RouterOS bajo Safe Mode o aprobación.",
    },
    {
        "key": "WEBFIG_L2_UNIVERSAL",
        "label": "Motor Universal Capa 2 (Bridges / VLANs / WireGuard)",
        "category": "Configuración y Control de Red",
        "description": "Gestión de switching, túneles WireGuard, MPLS y recursos Capa 2.",
    },
    {
        "key": "MANUAL_BACKUP_DIFF_GIT",
        "label": "Respaldos Manuales y Comparador Git Diff",
        "category": "Operaciones e Inventario",
        "description": "Generación de snapshots RSC, comparador visual y descarga cifrada.",
    },
    {
        "key": "RESTORE_BACKUP_CUSTOM_SCRIPT",
        "label": "Restauración de Scripts RSC y Backups",
        "category": "Configuración y Control de Red",
        "description": "Aplicación de configuraciones históricas o scripts personalizados.",
    },
    {
        "key": "BULK_ACTIONS_UPGRADE_ROS",
        "label": "Acciones Masivas y Actualizaciones RouterOS",
        "category": "Operaciones e Inventario",
        "description": "Ejecución por lote de comandos y upgrade de firmware en flota.",
    },
    {
        "key": "APPROVE_MAKER_CHECKER",
        "label": "Aprobación Maker-Checker (Cuatro Ojos)",
        "category": "Operaciones e Inventario",
        "description": "Autorización formal de solicitudes de cambio interceptadas con HTTP 202.",
    },
    {
        "key": "AUDIT_LOGS_QUERY",
        "label": "Consulta Forense de Auditoría WORM",
        "category": "Administración y Seguridad",
        "description": "Verificación de integridad de cadena SHA-256 y exportación firmada.",
    },
]


class UpdateRolePermissionsRequest(BaseModel):
    permissions: dict[str, str] = Field(
        ...,
        description="Diccionario de acciones y nivel de permiso (ALLOW, MAKER_CHECKER, READ_ONLY, DENY)",
    )


async def _get_tenant_role_overrides(tenant_id: str, role_value: str) -> dict[str, str] | None:
    try:
        redis = get_redis_client()
        key = f"rosgrid:{tenant_id}:rbac:{role_value}"
        raw = await redis.get(key)
        if raw:
            return cast(dict[str, str], json.loads(raw))
    except Exception as exc:
        logger.warning("Fallo al leer overrides de RBAC en KeyDB: %s", exc)
    return None


@router.get("/roles")
async def list_roles_and_permissions(
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.AUDITOR,
        )
    ),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
    """Devuelve los 11 roles del sistema con sus metadatos, descripciones y matriz de permisos."""
    tenant_id = str(claims["tid"])
    is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    await set_tenant_context(db, uuid.UUID(tenant_id), is_superadmin=is_sa)

    result = []
    for role_enum in SystemRoleEnum:
        meta = ROLE_METADATA.get(role_enum, {})
        base_perms = dict(POLICY_MATRIX.get(role_enum, {}))

        # Comprobar si existen modificaciones personalizadas guardadas para este tenant
        overrides = await _get_tenant_role_overrides(tenant_id, role_enum.value)
        effective_perms = {**base_perms, **(overrides or {})}

        result.append(
            {
                "role": role_enum.value,
                "title": meta.get("title", role_enum.value),
                "description": meta.get("description", "Sin descripción"),
                "level": meta.get("level", 99),
                "badge_color": meta.get("badge_color", "slate"),
                "is_system_reserved": meta.get("is_system_reserved", False),
                "has_custom_overrides": overrides is not None,
                "permissions": effective_perms,
            }
        )

    result.sort(key=lambda x: x["level"])
    return result


@router.get("/actions")
async def list_actions_metadata(
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.AUDITOR,
        )
    ),
) -> list[dict[str, Any]]:
    """Devuelve el catálogo de 19 acciones auditables y configurables."""
    return ACTIONS_METADATA


@router.put("/roles/{role_name}/permissions")
async def update_role_permissions(
    role_name: str,
    payload: UpdateRolePermissionsRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Define o modifica la matriz de permisos para un rol específico en el tenant."""
    try:
        target_role = SystemRoleEnum(role_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Rol '{role_name}' inválido o no reconocido") from e

    if target_role == SystemRoleEnum.SUPERADMIN_GLOBAL:
        raise HTTPException(
            status_code=403,
            detail="El rol SUPERADMIN_GLOBAL es inmutable y está reservado por el núcleo de seguridad",
        )

    valid_levels = {ALLOW, MAKER_CHECKER, READ_ONLY, DENY}
    sanitized_perms = {}
    valid_action_keys = {a["key"] for a in ACTIONS_METADATA}

    for action_key, level in payload.permissions.items():
        if action_key in valid_action_keys:
            if level not in valid_levels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Nivel de permiso '{level}' inválido para '{action_key}'. Válidos: {list(valid_levels)}",
                )
            sanitized_perms[action_key] = level

    tenant_id = str(claims["tid"])
    redis = get_redis_client()
    key = f"rosgrid:{tenant_id}:rbac:{target_role.value}"
    await redis.set(key, json.dumps(sanitized_perms))

    logger.info(
        "Permisos del rol %s actualizados por operador %s en tenant %s",
        target_role.value,
        claims.get("sub"),
        tenant_id,
    )

    return {
        "status": "success",
        "role": target_role.value,
        "message": f"Permisos del perfil {target_role.value} actualizados exitosamente para la organización.",
        "permissions": sanitized_perms,
    }


@router.post("/roles/{role_name}/reset")
async def reset_role_permissions(
    role_name: str,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
        )
    ),
) -> dict[str, Any]:
    """Restaura los permisos de un rol a la matriz predeterminada de fábrica."""
    try:
        target_role = SystemRoleEnum(role_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Rol '{role_name}' inválido") from e

    tenant_id = str(claims["tid"])
    redis = get_redis_client()
    key = f"rosgrid:{tenant_id}:rbac:{target_role.value}"
    await redis.delete(key)

    default_perms = POLICY_MATRIX.get(target_role, {})

    return {
        "status": "success",
        "role": target_role.value,
        "message": f"Permisos del rol {target_role.value} restaurados a los valores estándar de fábrica.",
        "permissions": default_perms,
    }
