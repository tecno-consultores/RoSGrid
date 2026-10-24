# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Gestión de Plantillas (Golden Configs), Acciones Masivas y Actualizador Centralizado de RouterOS v7."""

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import require_roles
from src.api.v1.webfig_common import _create_client_from_vault, get_router_and_client
from src.core.audit import write_audit_log
from src.core.crypto import encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikApiError, MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterTag
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    BulkJob,
    BulkJobItem,
    BulkJobStatusEnum,
    ConfigTemplate,
    CriticalActionTypeEnum,
    RouterBackup,
)
from src.schemas.bulk_and_updates import (
    BulkJobCreateRequest,
    BulkJobDetailResponse,
    BulkJobItemResponse,
    ConfigTemplateCreateRequest,
    ConfigTemplatePresetResponse,
    ConfigTemplateResponse,
    ConfigTemplateUpdateRequest,
    RosFleetUpdateStatusResponse,
    RosUpdateExecuteRequest,
    RosUpdateExecuteResponse,
    RosUpdateRouterStatus,
    TemplateRenderPreviewRequest,
    TemplateRenderPreviewResponse,
)
from src.services.poe_aware_upgrade import evaluate_safety_stop, order_routers_by_poe_stages
from src.services.topology_l2 import get_cached_topology

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations", tags=["Bulk Operations & Updates"])

_OPERATOR_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
    SystemRoleEnum.SUPPORT_L2,
)

_ADMIN_OPERATIONS_ROLES = (
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.SUPPORT_L3,
)


def _render_template_steps(steps: list[dict[str, Any]], vars_dict: dict[str, Any]) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    raw_str = json.dumps(steps)
    for k, v in vars_dict.items():
        variants = {str(k), str(k).upper(), str(k).lower()}
        for var_key in variants:
            placeholder = f"{{{{ {var_key} }}}}"
            raw_str = raw_str.replace(placeholder, str(v))
            placeholder_no_space = f"{{{{{var_key}}}}}"
            raw_str = raw_str.replace(placeholder_no_space, str(v))
    rendered = json.loads(raw_str)
    return rendered


async def _resolve_target_router_ids(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    req: BulkJobCreateRequest,
) -> list[uuid.UUID]:
    if req.target_router_ids:
        return [uuid.UUID(r) for r in req.target_router_ids]
    if req.target_role:
        stmt = select(Router.id).where(
            Router.tenant_id == tenant_id,
            Router.network_role == req.target_role,
        )
        return list((await db.execute(stmt)).scalars().all())
    if req.target_tag:
        stmt = (
            select(RouterTag.router_id)
            .where(RouterTag.tenant_id == tenant_id, RouterTag.tag_name == req.target_tag)
            .distinct()
        )
        return list((await db.execute(stmt)).scalars().all())
    raise HTTPException(status_code=400, detail="Debe especificar target_router_ids, target_role o target_tag")


async def _perform_pre_upgrade_backup(
    client: MikrotikRestClient,
    router_obj: Router,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    try:
        raw_res = await client.post("export", {"terse": "false", "show-sensitive": "false"})
        raw_text = str(raw_res) if not isinstance(raw_res, str) else raw_res
        lines = [ln for ln in raw_text.splitlines() if not ln.strip().startswith("#")]
        cleaned = "\n".join(lines).strip()
        rsc_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

        aad = f"{tenant_id}:{router_obj.id}".encode()
        ct, iv, tag = encrypt_aes_gcm(cleaned.encode("utf-8"), aad)
        now_utc = datetime.now(UTC)

        backup = RouterBackup(
            tenant_id=tenant_id,
            router_id=router_obj.id,
            backup_type="PRE_UPGRADE",
            ros_version_at_backup=router_obj.ros_version or "7.16",
            rsc_sha256_hash=rsc_hash,
            rsc_size_bytes=len(cleaned.encode("utf-8")),
            rsc_ciphertext=ct,
            rsc_iv=iv,
            rsc_tag=tag,
            diff_lines_added=0,
            diff_lines_removed=0,
            triggered_by=user_id,
            created_at=now_utc,
            last_verified_identical_at=now_utc,
            expires_at=now_utc + timedelta(days=30),
        )
        db.add(backup)
        await db.flush()
        return True
    except Exception as exc:
        logger.error("Fallo de backup obligatorio previo al upgrade en %s: %s", router_obj.display_name, exc)
        return False


# ============================================================================
# PLANTILLAS (GOLDEN CONFIGS)
# ============================================================================

_DEFAULT_STARTER_TEMPLATES = [
    {
        "name": "CLIENTE_NTP",
        "category": "SYSTEM",
        "description": "Activa el cliente NTP",
        "ros_command_template": (
            "/system ntp client set enabled=yes\n"
            "/system ntp client servers add address={{ ntp_server_0 }}\n"
            "/system ntp client servers add address={{ ntp_server_1 }}\n"
            "/system ntp client servers add address={{ ntp_server_2 }}\n"
            "/system ntp client servers add address={{ ntp_server_3 }}"
        ),
        "variables_schema": [
            {
                "key": "ntp_server_0",
                "label": "Servidor NTP Pool 0",
                "default_val": "0.pool.ntp.org",
                "var_type": "string",
            },
            {
                "key": "ntp_server_1",
                "label": "Servidor NTP Pool 1",
                "default_val": "1.pool.ntp.org",
                "var_type": "string",
            },
            {
                "key": "ntp_server_2",
                "label": "Servidor NTP Pool 2",
                "default_val": "2.pool.ntp.org",
                "var_type": "string",
            },
            {
                "key": "ntp_server_3",
                "label": "Servidor NTP Pool 3",
                "default_val": "3.pool.ntp.org",
                "var_type": "string",
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "system/ntp/client/set",
                "payload": {"enabled": "yes"},
                "cli_command": "/system ntp client set enabled=yes",
            },
            {
                "method": "PUT",
                "endpoint": "system/ntp/client/servers",
                "payload": {"address": "{{ ntp_server_0 }}"},
                "cli_command": "/system ntp client servers add address={{ ntp_server_0 }}",
            },
            {
                "method": "PUT",
                "endpoint": "system/ntp/client/servers",
                "payload": {"address": "{{ ntp_server_1 }}"},
                "cli_command": "/system ntp client servers add address={{ ntp_server_1 }}",
            },
            {
                "method": "PUT",
                "endpoint": "system/ntp/client/servers",
                "payload": {"address": "{{ ntp_server_2 }}"},
                "cli_command": "/system ntp client servers add address={{ ntp_server_2 }}",
            },
            {
                "method": "PUT",
                "endpoint": "system/ntp/client/servers",
                "payload": {"address": "{{ ntp_server_3 }}"},
                "cli_command": "/system ntp client servers add address={{ ntp_server_3 }}",
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "DNS_CORPORATIVO_RESILIENTE",
        "category": "NETWORK",
        "description": "Configura servidores DNS redundantes (Quad9 y Cloudflare) y vacía la caché de resolución.",
        "ros_command_template": (
            "/ip dns set servers={{ dns_servers }} allow-remote-requests={{ allow_remote }}\n/ip dns cache flush"
        ),
        "variables_schema": [
            {
                "key": "dns_servers",
                "label": "Servidores DNS (separados por coma)",
                "default_val": "9.9.9.9,1.1.1.1",
                "var_type": "string",
            },
            {"key": "allow_remote", "label": "Permitir peticiones remotas", "default_val": "no", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "ip/dns/set",
                "payload": {"servers": "{{ dns_servers }}", "allow-remote-requests": "{{ allow_remote }}"},
                "cli_command": "/ip dns set servers={{ dns_servers }} allow-remote-requests={{ allow_remote }}",
            },
            {
                "method": "POST",
                "endpoint": "ip/dns/cache/flush",
                "payload": {},
                "cli_command": "/ip dns cache flush",
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "SNMP_V2C_MONITOREO_NOC",
        "category": "SECURITY",
        "description": "Configura comunidad SNMP v2c para supervisión y telemetría desde el Wallboard NOC.",
        "ros_command_template": (
            "/snmp set enabled=yes\n"
            "/snmp community set [find default=yes] name={{ snmp_community }} addresses={{ snmp_addresses }}"
        ),
        "variables_schema": [
            {
                "key": "snmp_community",
                "label": "Nombre de Comunidad SNMP",
                "default_val": "RoSGrid_NOC",
                "var_type": "string",
            },
            {
                "key": "snmp_addresses",
                "label": "Subredes autorizadas (separadas por coma)",
                "default_val": "10.0.0.0/8,192.168.0.0/16",
                "var_type": "string",
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "snmp/set",
                "payload": {"enabled": "yes"},
                "cli_command": "/snmp set enabled=yes",
            },
            {
                "method": "PATCH",
                "endpoint": "snmp/community/*0",
                "payload": {"name": "{{ snmp_community }}", "addresses": "{{ snmp_addresses }}"},
                "cli_command": (
                    "/snmp community set [find default=yes] name={{ snmp_community }} addresses={{ snmp_addresses }}"
                ),
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "SYSLOG_CENTRALIZADO_ROSGRID",
        "category": "SECURITY",
        "description": (
            "Configura el reenvío de logs críticos y de seguridad vía Syslog remoto hacia el receptor centralizado de RoSGrid."
        ),
        "ros_command_template": (
            '/system logging action remove [find name="rosgridsyslog"]\n'
            '/system logging action add name="rosgridsyslog" target=remote remote={{ rosgrid_server_ip }} remote-port={{ rosgrid_syslog_port }} remote-log-format=syslog syslog-facility=daemon\n'
            '/system logging remove [find action="rosgridsyslog"]\n'
            '/system logging add topics=interface,warning,critical action="rosgridsyslog"\n'
            '/system logging add topics=route,bgp,warning action="rosgridsyslog"\n'
            '/system logging add topics=route,ospf,warning action="rosgridsyslog"\n'
            '/system logging add topics=system,error,critical action="rosgridsyslog"\n'
            '/system logging add topics=dhcp,critical action="rosgridsyslog"\n'
            '/system logging add topics=firewall,warning action="rosgridsyslog"'
        ),
        "variables_schema": [
            {
                "key": "rosgrid_server_ip",
                "label": "Dirección IP Servidor RoSGrid",
                "default_val": "192.168.1.100",
                "var_type": "string",
            },
            {
                "key": "rosgrid_syslog_port",
                "label": "Puerto UDP Syslog RoSGrid",
                "default_val": "5514",
                "var_type": "string",
            },
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "system/logging/action",
                "payload": {
                    "name": "rosgridsyslog",
                    "target": "remote",
                    "remote": "{{ rosgrid_server_ip }}",
                    "remote-port": "{{ rosgrid_syslog_port }}",
                    "remote-log-format": "syslog",
                    "syslog-facility": "daemon",
                },
                "cli_command": (
                    '/system logging action add name="rosgridsyslog" target=remote '
                    "remote={{ rosgrid_server_ip }} remote-port={{ rosgrid_syslog_port }} "
                    'remote-log-format=syslog syslog-facility=daemon'
                ),
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "interface,warning,critical", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=interface,warning,critical action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "route,bgp,warning", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=route,bgp,warning action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "route,ospf,warning", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=route,ospf,warning action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "system,error,critical", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=system,error,critical action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "dhcp,critical", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=dhcp,critical action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "firewall,warning", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=firewall,warning action="rosgridsyslog"',
            },
        ],
        "requires_safemode": True,
    },
]


@router.get("/templates", response_model=list[ConfigTemplateResponse])
async def list_templates(
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[ConfigTemplateResponse]:
    """Lista plantillas de configuración del Tenant. Si no existen, inicializa plantillas base sugeridas."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    stmt = select(ConfigTemplate).where(ConfigTemplate.tenant_id == tenant_id).order_by(ConfigTemplate.name)
    templates = list((await db.execute(stmt)).scalars().all())

    if not templates:
        for starter in _DEFAULT_STARTER_TEMPLATES:
            tpl = ConfigTemplate(
                tenant_id=tenant_id,
                name=starter["name"],
                category=starter["category"],
                description=starter["description"],
                variables_schema=starter["variables_schema"],
                rest_steps_template=starter["rest_steps_template"],
                requires_safemode=starter["requires_safemode"],
                created_by=user_id,
            )
            db.add(tpl)
        await db.commit()
        templates = list((await db.execute(stmt)).scalars().all())

    return [
        ConfigTemplateResponse(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            category=t.category,
            description=t.description,
            variables_schema=t.variables_schema,
            rest_steps_template=t.rest_steps_template,
            requires_safemode=t.requires_safemode,
            created_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]


@router.get("/templates/presets", response_model=list[ConfigTemplatePresetResponse])
async def list_template_presets(
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
) -> list[dict[str, Any]]:
    """Devuelve el catálogo de plantillas predefinidas recomendadas de RouterOS v7."""
    return _DEFAULT_STARTER_TEMPLATES


@router.post("/templates/seed-defaults", response_model=list[ConfigTemplateResponse])
async def seed_default_templates(
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[ConfigTemplateResponse]:
    """Siembra las plantillas predefinidas del sistema que no existan aún en el Tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    stmt = select(ConfigTemplate).where(ConfigTemplate.tenant_id == tenant_id).order_by(ConfigTemplate.name)
    templates = list((await db.execute(stmt)).scalars().all())
    existing_names = {t.name for t in templates}

    added = False
    for starter in _DEFAULT_STARTER_TEMPLATES:
        if starter["name"] not in existing_names:
            tpl = ConfigTemplate(
                tenant_id=tenant_id,
                name=starter["name"],
                category=starter["category"],
                description=starter["description"],
                variables_schema=starter["variables_schema"],
                rest_steps_template=starter["rest_steps_template"],
                requires_safemode=starter["requires_safemode"],
                created_by=user_id,
            )
            db.add(tpl)
            added = True

    if added:
        await db.commit()
        templates = list((await db.execute(stmt)).scalars().all())

    return [
        ConfigTemplateResponse(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            category=t.category,
            description=t.description,
            variables_schema=t.variables_schema,
            rest_steps_template=t.rest_steps_template,
            requires_safemode=t.requires_safemode,
            created_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]


@router.get("/templates/{template_id}", response_model=ConfigTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ConfigTemplateResponse:
    """Obtiene el detalle completo de una plantilla."""
    tenant_id = uuid.UUID(claims["tid"])
    template = await db.get(ConfigTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    return ConfigTemplateResponse(
        id=template.id,
        tenant_id=template.tenant_id,
        name=template.name,
        category=template.category,
        description=template.description,
        variables_schema=template.variables_schema,
        rest_steps_template=template.rest_steps_template,
        requires_safemode=template.requires_safemode,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/templates", response_model=ConfigTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: ConfigTemplateCreateRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ConfigTemplateResponse:
    """Crea una nueva plantilla parametrizable Golden Config."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])

    existing = await db.execute(
        select(ConfigTemplate).where(
            ConfigTemplate.tenant_id == tenant_id,
            ConfigTemplate.name == payload.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Ya existe una plantilla con el nombre '{payload.name}'")

    template = ConfigTemplate(
        tenant_id=tenant_id,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        variables_schema=payload.variables_schema,
        rest_steps_template=payload.rest_steps_template,
        requires_safemode=payload.requires_safemode,
        created_by=user_id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    ip_addr = request.client.host if (request and request.client) else "127.0.0.1"
    ua = request.headers.get("User-Agent") if request else "Internal/UnitTests"
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="OPERATIONS",
        event_action="CONFIG_TEMPLATE_CREATED",
        after_state={"template_id": str(template.id), "name": template.name, "category": template.category},
    )
    await db.commit()

    return ConfigTemplateResponse(
        id=template.id,
        tenant_id=template.tenant_id,
        name=template.name,
        category=template.category,
        description=template.description,
        variables_schema=template.variables_schema,
        rest_steps_template=template.rest_steps_template,
        requires_safemode=template.requires_safemode,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put("/templates/{template_id}", response_model=ConfigTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    payload: ConfigTemplateUpdateRequest,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> ConfigTemplateResponse:
    """Actualiza una plantilla Golden Config existente."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    template = await db.get(ConfigTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    if payload.name is not None and payload.name != template.name:
        existing = await db.execute(
            select(ConfigTemplate).where(
                ConfigTemplate.tenant_id == tenant_id,
                ConfigTemplate.name == payload.name,
                ConfigTemplate.id != template_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Ya existe una plantilla con el nombre '{payload.name}'")
        template.name = payload.name

    if payload.category is not None:
        template.category = payload.category
    if payload.description is not None:
        template.description = payload.description
    if payload.variables_schema is not None:
        template.variables_schema = payload.variables_schema
    if payload.rest_steps_template is not None:
        template.rest_steps_template = payload.rest_steps_template
    if payload.requires_safemode is not None:
        template.requires_safemode = payload.requires_safemode

    template.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(template)

    ip_addr = request.client.host if (request and request.client) else "127.0.0.1"
    ua = request.headers.get("User-Agent") if request else "Internal/UnitTests"
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="OPERATIONS",
        event_action="CONFIG_TEMPLATE_UPDATED",
        after_state={"template_id": str(template.id), "name": template.name, "category": template.category},
    )
    await db.commit()

    return ConfigTemplateResponse(
        id=template.id,
        tenant_id=template.tenant_id,
        name=template.name,
        category=template.category,
        description=template.description,
        variables_schema=template.variables_schema,
        rest_steps_template=template.rest_steps_template,
        requires_safemode=template.requires_safemode,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    request: Request,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> None:
    """Elimina una plantilla Golden Config."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    template = await db.get(ConfigTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    tpl_name = template.name
    await db.delete(template)
    await db.commit()

    ip_addr = request.client.host if (request and request.client) else "127.0.0.1"
    ua = request.headers.get("User-Agent") if request else "Internal/UnitTests"
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="OPERATIONS",
        event_action="CONFIG_TEMPLATE_DELETED",
        before_state={"template_id": str(template_id), "name": tpl_name},
    )
    await db.commit()


@router.post("/templates/{template_id}/render-preview", response_model=TemplateRenderPreviewResponse)
async def preview_template(
    template_id: uuid.UUID,
    payload: TemplateRenderPreviewRequest,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> TemplateRenderPreviewResponse:
    """Renderiza los pasos REST sustituyendo variables sin tocar ningún router."""
    tenant_id = uuid.UUID(claims["tid"])
    template = await db.get(ConfigTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    rendered = _render_template_steps(template.rest_steps_template, payload.variables)
    return TemplateRenderPreviewResponse(rendered_steps=rendered)


# ============================================================================
# TRABAJOS MASIVOS MULTI-ROUTER (BULK JOBS)
# ============================================================================


async def _execute_single_step(client: MikrotikRestClient, step: dict[str, Any]) -> Any:
    """Ejecuta un paso individual REST tolerando endpoints singulares e idempotencia en RouterOS v7."""
    method = step.get("method", "PATCH").upper()
    endpoint = step.get("endpoint", "").strip("/")
    payload = step.get("payload", {})

    # Auto-redirección de endpoints singulares que no admiten PATCH en RouterOS v7
    if endpoint == "snmp" and method in ("PATCH", "POST"):
        return await client.post("snmp/set", payload)
    if endpoint == "system/ntp/client" and method in ("PATCH", "POST"):
        return await client.post("system/ntp/client/set", payload)
    if endpoint == "ip/dns" and method in ("PATCH", "POST"):
        return await client.post("ip/dns/set", payload)

    if method == "PUT":
        try:
            return await client.put(endpoint, payload)
        except MikrotikApiError as err:
            err_msg = str(err).lower()
            # Idempotencia para /system/logging/action si ya existe una acción con ese nombre
            if "already exists" in err_msg and endpoint == "system/logging/action":
                act_name = payload.get("name")
                if act_name:
                    actions = await client.get("system/logging/action")
                    if isinstance(actions, list):
                        match_act = next((a for a in actions if a.get("name") == act_name), None)
                        if match_act and ".id" in match_act:
                            return await client.patch(f"system/logging/action/{match_act['.id']}", payload)
            # Idempotencia para /system/ntp/client/servers si ya existe la dirección registrada
            if "duplicate address" in err_msg and endpoint == "system/ntp/client/servers":
                logger.info("Servidor NTP ya registrado en router, ignorando duplicado: %s", payload.get("address"))
                return []
            raise
    elif method == "POST":
        return await client.post(endpoint, payload)
    elif method == "DELETE":
        return await client.delete(endpoint)
    elif method == "PATCH":
        # Resolución dinámica de la comunidad default si *0 no existe o devuelve 404
        if endpoint.startswith("snmp/community/"):
            try:
                return await client.patch(endpoint, payload)
            except MikrotikApiError as err:
                if "not found" in str(err).lower() or "404" in str(err) or "invalid" in str(err).lower():
                    comms = await client.get("snmp/community")
                    if isinstance(comms, list) and comms:
                        def_c = next((c for c in comms if c.get("default") == "true"), comms[0])
                        if ".id" in def_c:
                            return await client.patch(f"snmp/community/{def_c['.id']}", payload)
                raise

        try:
            return await client.patch(endpoint, payload)
        except MikrotikApiError as err:
            err_str = str(err).lower()
            # Fallback para menús singulares de RouterOS v7 (ej. system/ntp/client, ip/dns, snmp)
            # donde RouterOS espera POST <endpoint>/set en lugar de PATCH
            if (
                "missing or invalid resource identifier" in err_str
                or "500" in err_str
                or "internal server error" in err_str
                or endpoint in ("snmp", "system/ntp/client", "ip/dns")
            ):
                return await client.post(f"{endpoint}/set", payload)
            raise
    elif method == "GET":
        return await client.get(endpoint)
    else:
        raise ValueError(f"Método REST no soportado: {method}")


async def execute_bulk_job_on_fleet(
    job: BulkJob,
    db: AsyncSession,
    claims: dict[str, Any] | None = None,
) -> BulkJob:
    """Ejecuta una acción masiva multi-router aplicando la plantilla sobre cada router objetivo."""
    job.status = BulkJobStatusEnum.RUNNING
    job.started_at = datetime.now(UTC)
    await db.flush()

    template: ConfigTemplate | None = None
    if job.template_id:
        obj = await db.get(ConfigTemplate, job.template_id)
        if isinstance(obj, ConfigTemplate):
            template = obj

    rest_steps_template: list[dict[str, Any]] = []
    if template and getattr(template, "rest_steps_template", None):
        rest_steps_template = list(template.rest_steps_template)
    else:
        # Búsqueda fallback por nombre de plantilla predefinida en el catálogo
        title_str = str(job.title or "")
        for st in _DEFAULT_STARTER_TEMPLATES:
            if str(st["name"]) in title_str:
                raw_steps = st["rest_steps_template"]
                if isinstance(raw_steps, list):
                    rest_steps_template = [dict(s) for s in raw_steps]
                break

    vars_dict: dict[str, Any] = {}
    if job.execution_parameters and isinstance(job.execution_parameters, dict):
        raw_vars = job.execution_parameters.get("variables", {})
        if isinstance(raw_vars, dict):
            vars_dict = raw_vars

    rendered_steps = _render_template_steps(rest_steps_template, vars_dict) if rest_steps_template else []

    stmt_items = select(BulkJobItem).where(BulkJobItem.bulk_job_id == job.id)
    items_map: dict[uuid.UUID, BulkJobItem] = {
        i.router_id: i for i in (await db.execute(stmt_items)).scalars().all()
    }

    succeeded_count = 0
    failed_count = 0

    for rid_str in (job.target_router_ids or []):
        try:
            rid = uuid.UUID(str(rid_str))
        except Exception:
            continue

        item = items_map.get(rid)
        if not item:
            item = BulkJobItem(
                tenant_id=job.tenant_id,
                bulk_job_id=job.id,
                router_id=rid,
                status="PENDING",
            )
            db.add(item)
            await db.flush()

        item.status = "IN_PROGRESS"
        item.started_at = datetime.now(UTC)
        await db.flush()

        stmt_r = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.id == rid, Router.tenant_id == job.tenant_id)
        )
        router_obj = (await db.execute(stmt_r)).scalar_one_or_none()

        if not router_obj or not router_obj.vault:
            item.status = "FAILED"
            item.error_detail = "Router no encontrado o sin credenciales en bóveda"
            item.finished_at = datetime.now(UTC)
            failed_count += 1
            await db.flush()
            continue

        client: MikrotikRestClient | None = None
        try:
            client = _create_client_from_vault(router_obj, job.tenant_id)
            for step in rendered_steps:
                await _execute_single_step(client, step)

            item.status = "SUCCESS"
            item.response_summary = {"message": f"Aplicados {len(rendered_steps)} pasos con éxito"}
            item.error_detail = None
            succeeded_count += 1
        except Exception as exc:
            logger.error("Error al aplicar plantilla en router %s (%s): %s", router_obj.display_name, rid_str, exc)
            item.status = "FAILED"
            item.error_detail = str(exc)
            failed_count += 1
        finally:
            if client:
                await client.close()
            item.finished_at = datetime.now(UTC)
            await db.flush()

    job.succeeded_count = succeeded_count
    job.failed_count = failed_count
    job.completed_at = datetime.now(UTC)
    if failed_count == 0 and succeeded_count > 0:
        job.status = BulkJobStatusEnum.COMPLETED
    elif succeeded_count > 0:
        job.status = BulkJobStatusEnum.PARTIAL_FAILURE
    else:
        job.status = BulkJobStatusEnum.FAILED

    await db.flush()
    return job


@router.post("/bulk-jobs", response_model=BulkJobDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_job(
    payload: BulkJobCreateRequest,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BulkJobDetailResponse:
    """Crea una acción masiva multi-router con intercepción Maker-Checker si el rol es SUPPORT_L2."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    role = claims.get("rol")

    target_ids = await _resolve_target_router_ids(db, tenant_id, payload)
    if not target_ids:
        raise HTTPException(status_code=400, detail="No se encontraron routers objetivo con los criterios dados")

    is_l2 = role == SystemRoleEnum.SUPPORT_L2.value
    job_status = BulkJobStatusEnum.AWAITING_APPROVAL if is_l2 else BulkJobStatusEnum.QUEUED

    approval_req_id: uuid.UUID | None = None
    if is_l2:
        now_utc = datetime.now(UTC)
        app_req = ApprovalRequest(
            tenant_id=tenant_id,
            action_type=CriticalActionTypeEnum.BULK_MULTI_ROUTER_EXECUTION,
            status=ApprovalStatusEnum.PENDING,
            summary=f"Acción masiva: {payload.title} sobre {len(target_ids)} routers",
            requester_justification="Solicitud de ejecución masiva generada por Soporte N2",
            ros_rest_method="BULK",
            ros_rest_path="/operations/bulk-jobs",
            request_payload={"parameters": payload.execution_parameters},
            requested_by=user_id,
            expires_at=now_utc + timedelta(hours=24),
        )
        db.add(app_req)
        await db.flush()
        approval_req_id = app_req.id

    bulk_job = BulkJob(
        tenant_id=tenant_id,
        job_type=payload.job_type,
        title=payload.title,
        status=job_status,
        template_id=payload.template_id,
        execution_parameters=payload.execution_parameters,
        target_router_ids=[str(rid) for rid in target_ids],
        total_routers=len(target_ids),
        succeeded_count=0,
        failed_count=0,
        approval_request_id=approval_req_id,
        created_by=user_id,
    )
    db.add(bulk_job)
    await db.flush()

    for rid in target_ids:
        item = BulkJobItem(
            tenant_id=tenant_id,
            bulk_job_id=bulk_job.id,
            router_id=rid,
            status="PENDING",
        )
        db.add(item)

    await db.commit()
    await db.refresh(bulk_job)

    # Si no requiere aprobación Maker-Checker, despachar inmediatamente en la flota
    if not is_l2:
        bulk_job = await execute_bulk_job_on_fleet(bulk_job, db, claims)
        await db.commit()
        await db.refresh(bulk_job)

    return await get_bulk_job(bulk_job.id, claims, db)


@router.get("/bulk-jobs/{job_id}", response_model=BulkJobDetailResponse)
async def get_bulk_job(
    job_id: uuid.UUID,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> BulkJobDetailResponse:
    """Consulta el progreso en vivo de un trabajo masivo y el estado router por router."""
    tenant_id = uuid.UUID(claims["tid"])
    job = await db.get(BulkJob, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Trabajo masivo no encontrado")

    stmt = select(BulkJobItem).where(BulkJobItem.bulk_job_id == job_id)
    raw_items = (await db.execute(stmt)).scalars().all()

    items = [
        BulkJobItemResponse(
            id=i.id,
            router_id=i.router_id,
            status=i.status,
            response_summary=i.response_summary,
            error_detail=i.error_detail,
            started_at=i.started_at,
            finished_at=i.finished_at,
        )
        for i in raw_items
    ]

    return BulkJobDetailResponse(
        id=job.id,
        tenant_id=job.tenant_id,
        job_type=job.job_type,
        title=job.title,
        status=job.status.value,
        template_id=job.template_id,
        execution_parameters=job.execution_parameters,
        target_router_ids=job.target_router_ids,
        total_routers=job.total_routers,
        succeeded_count=job.succeeded_count,
        failed_count=job.failed_count,
        approval_request_id=job.approval_request_id,
        created_by=job.created_by,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        items=items,
    )


# ============================================================================
# ACTUALIZACIÓN CENTRALIZADA DE ROUTEROS v7 Y ROUTERBOOT
# ============================================================================


@router.get("/ros-updates/status", response_model=RosFleetUpdateStatusResponse)
async def get_fleet_updates_status(
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RosFleetUpdateStatusResponse:
    """Resumen de versiones de RouterOS y Firmware de toda la flota del Tenant."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(Router).where(Router.tenant_id == tenant_id).order_by(Router.display_name)
    routers = (await db.execute(stmt)).scalars().all()

    statuses: list[RosUpdateRouterStatus] = []
    pending_count = 0
    up_to_date_count = 0

    for r in routers:
        has_update = False
        if (
            r.update_available_version
            and r.update_available_version != r.ros_version
            or r.upgrade_firmware_version
            and r.upgrade_firmware_version != r.firmware_version
        ):
            has_update = True

        if has_update:
            pending_count += 1
        else:
            up_to_date_count += 1

        statuses.append(
            RosUpdateRouterStatus(
                router_id=r.id,
                display_name=r.display_name,
                ros_version=r.ros_version,
                update_available_version=r.update_available_version,
                firmware_version=r.firmware_version,
                upgrade_firmware_version=r.upgrade_firmware_version,
                has_update=has_update,
            )
        )

    return RosFleetUpdateStatusResponse(
        total_routers=len(routers),
        up_to_date_count=up_to_date_count,
        pending_update_count=pending_count,
        routers=statuses,
    )


async def _resolve_upgrade_stages(
    tenant_id: uuid.UUID,
    router_ids: list[uuid.UUID],
    poe_aware: bool,
) -> list[list[uuid.UUID]]:
    """Determina las etapas ordenadas por PoE o etapa única."""
    if not poe_aware:
        return [router_ids]
    cached = await get_cached_topology(tenant_id)
    edges = cached.edges if cached else []
    return order_routers_by_poe_stages(router_ids, edges)


async def _execute_single_router_upgrade(
    rid: uuid.UUID,
    payload: RosUpdateExecuteRequest,
    claims: dict[str, Any],
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    stage_idx: int,
) -> tuple[dict[str, Any], bool]:
    """Ejecuta backup e instalación para un router individual. Retorna (resultado, fue_exitoso)."""
    try:
        r_obj, client = await get_router_and_client(rid, claims, db)
        backup_ok = await _perform_pre_upgrade_backup(client, r_obj, tenant_id, user_id, db)
        if not backup_ok:
            return {"router_id": str(rid), "status": "ABORTED_PRE_BACKUP_FAILED", "stage": stage_idx}, False

        if payload.auto_upgrade_firmware:
            await client.patch("system/routerboard/settings", {"auto-upgrade": "yes"})

        update_res = await client.post("system/package/update/install", {})
        return {"router_id": str(rid), "status": "UPGRADE_TRIGGERED", "detail": update_res, "stage": stage_idx}, True
    except Exception as exc:
        return {"router_id": str(rid), "status": "FAILED", "error": str(exc), "stage": stage_idx}, False


async def _process_upgrade_stages(
    ordered_stages: list[list[uuid.UUID]],
    payload: RosUpdateExecuteRequest,
    claims: dict[str, Any],
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[list[dict[str, Any]], bool]:
    """Itera etapas aplicando Safety Stop."""
    results: list[dict[str, Any]] = []
    failed_count = 0
    total_processed = 0

    for stage_idx, stage in enumerate(ordered_stages):
        for rid in stage:
            total_processed += 1
            res_dict, ok = await _execute_single_router_upgrade(rid, payload, claims, db, tenant_id, user_id, stage_idx)
            results.append(res_dict)
            if not ok:
                failed_count += 1
            if evaluate_safety_stop(failed_count, total_processed, payload.safety_stop_threshold_percent):
                return results, True
    return results, False


@router.post("/ros-updates/execute", response_model=RosUpdateExecuteResponse)
async def execute_fleet_updates(
    payload: RosUpdateExecuteRequest,
    claims: dict[str, Any] = Depends(require_roles(*_ADMIN_OPERATIONS_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RosUpdateExecuteResponse:
    """Lanza la actualización segura de RouterOS con backup previo obligatorio y orden PoE-aware."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])

    ordered_stages = await _resolve_upgrade_stages(tenant_id, payload.router_ids, payload.poe_aware)
    results, safety_stop_triggered = await _process_upgrade_stages(
        ordered_stages, payload, claims, db, tenant_id, user_id
    )
    await db.commit()

    poe_stages = [[str(r) for r in s] for s in ordered_stages] if payload.poe_aware else None
    msg = f"Procesadas {len(results)}/{len(payload.router_ids)} solicitudes de actualización"
    if safety_stop_triggered:
        msg += " (Detenido por Safety Stop de flota)"

    return RosUpdateExecuteResponse(
        status="SAFETY_STOPPED" if safety_stop_triggered else "COMPLETED",
        message=msg,
        results=results,
        poe_stages=poe_stages,
        safety_stop_triggered=safety_stop_triggered,
    )
