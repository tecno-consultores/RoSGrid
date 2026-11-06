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
from src.mikrotik.client import (
    MikrotikApiError,
    MikrotikConnectionError,
    MikrotikRestClient,
    MikrotikTimeoutError,
)
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
    RosUpdateChannelCheckItem,
    RosUpdateChannelCheckRequest,
    RosUpdateChannelCheckResponse,
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


def _is_chr_router(router_obj: Router, rb_data: dict[str, Any] | None = None) -> bool:
    """Detecta determinísticamente si un equipo MikroTik es CHR (Cloud Hosted Router)."""
    board = (router_obj.board_name or "").upper()
    model = (router_obj.model_name or "").upper()
    if "CHR" in board or "CHR" in model:
        return True
    if isinstance(rb_data, dict):
        rb_flag = str(rb_data.get("routerboard", "")).strip().lower()
        if rb_flag in ("false", "no"):
            return True
    return False


def _should_skip_step_for_router(step: dict[str, Any], is_chr: bool, vars_dict: dict[str, Any]) -> bool:
    """Determina si un paso REST de RouterBOOT debe omitirse por tratarse de un CHR o estar desactivado."""
    endpoint = str(step.get("endpoint", "")).strip("/").lower()
    if not endpoint.startswith("system/routerboard"):
        return False
    if is_chr:
        return True
    upg_fw = str(vars_dict.get("upgrade_firmware", "yes")).strip().lower()
    return upg_fw in ("no", "false", "0")


def _extract_update_status_text(res: Any) -> str:
    """Extrae el texto de estado desde la respuesta de check-for-updates, install o package/update."""
    if isinstance(res, dict):
        return str(res.get("status") or "")
    if isinstance(res, list) and res:
        last = res[-1]
        if isinstance(last, dict):
            return str(last.get("status") or "")
    return ""


def _clean_version_token(ver: str | None) -> str:
    """Extrae de forma segura el token de versión (ej. '7.25.1 (stable)' -> '7.25.1') sin lanzar IndexError."""
    parts = (ver or "").split()
    return parts[0].strip() if parts else ""


def _resolve_npk_package_filename(version: str, architecture_name: str | None) -> str:
    """Determina el nombre oficial del paquete .npk de MikroTik según la arquitectura."""
    raw_arch = (architecture_name or "x86_64").strip().lower()
    arch_parts = raw_arch.split()
    arch = arch_parts[0] if arch_parts else "x86_64"
    if arch in ("x86_64", "x86", "chr", ""):
        return f"routeros-{version}.npk"
    return f"routeros-{version}-{arch}.npk"


async def _cleanup_corrupted_npk_downloads(client: MikrotikRestClient) -> int:
    """Elimina archivos .npk truncados (size == 0) en el router para evitar bloqueos de descarga."""
    removed = 0
    try:
        files = await client.get("file")
        if not isinstance(files, list):
            return 0
        for item in files:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            size = str(item.get("size", ""))
            fid = item.get(".id")
            if name.endswith(".npk") and size == "0" and fid:
                await client.delete(f"file/{fid}")
                removed += 1
    except Exception as exc:
        logger.debug("Omitida limpieza de .npk residuales: %s", exc)
    return removed


async def _fetch_latest_version_via_http_fallback(
    client: MikrotikRestClient,
    channel: str,
) -> str | None:
    """Consulta la versión más reciente vía /tool/fetch cuando RouterOS 7.25 cae en el bug 'bad HTTP response'."""
    try:
        res = await client.post(
            "tool/fetch",
            {
                "url": f"http://upgrade.mikrotik.com/routeros/NEWESTa7.{channel}",
                "output": "user",
            },
            timeout=20.0,
        )
        items = res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])
        for entry in reversed(items):
            if isinstance(entry, dict) and entry.get("data"):
                parts = str(entry["data"]).strip().split()
                if parts:
                    return parts[0].strip()
    except Exception as exc:
        logger.debug("Fallback /tool/fetch de versión falló: %s", exc)
    return None


async def _install_routeros_via_fetch_fallback(
    client: MikrotikRestClient,
    r_obj: Router,
    channel: str,
    target_version: str | None = None,
) -> dict[str, Any]:
    """Descarga el paquete .npk oficial vía /tool/fetch y reinicia el router cuando package/update está bloqueado."""
    ver = _clean_version_token(target_version)
    if not ver:
        ver = (await _fetch_latest_version_via_http_fallback(client, channel)) or ""
    if not ver:
        raise RuntimeError("No se pudo resolver la versión objetivo de RouterOS desde upgrade.mikrotik.com")

    clean_inst = _clean_version_token(r_obj.ros_version)
    if ver == clean_inst:
        return {"status": "UP_TO_DATE", "installed_version": clean_inst, "latest_version": ver}

    pkg_name = _resolve_npk_package_filename(ver, getattr(r_obj, "architecture_name", None))
    pkg_url = f"http://upgrade.mikrotik.com/routeros/{ver}/{pkg_name}"
    await client.post("tool/fetch", {"url": pkg_url, "dst-path": pkg_name}, timeout=180.0)

    try:
        await client.post("system/reboot", {})
    except (MikrotikConnectionError, MikrotikTimeoutError):
        logger.info("Router %s reiniciando tras descarga NPK directa (%s)", r_obj.display_name, pkg_name)

    r_obj.ros_version = ver
    r_obj.update_available_version = ver
    return {"status": "INSTALLED_VIA_FETCH_FALLBACK", "package": pkg_name, "target_version": ver}


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
            '/system logging add topics=firewall,warning action="rosgridsyslog"\n'
            '/system logging add topics=system,info action="rosgridsyslog"\n'
            '/system logging add topics=account action="rosgridsyslog"\n'
            '/system logging add topics=firewall,info action="rosgridsyslog"\n'
            '/system logging add topics=pppoe,ppp,info,warning,error action="rosgridsyslog"'
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
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "system,info", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=system,info action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "account", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=account action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "firewall,info", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=firewall,info action="rosgridsyslog"',
            },
            {
                "method": "PUT",
                "endpoint": "system/logging",
                "payload": {"topics": "pppoe,ppp,info,warning,error", "action": "rosgridsyslog"},
                "cli_command": '/system logging add topics=pppoe,ppp,info,warning,error action="rosgridsyslog"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "ISP_BGP_RPKI_STRICT_VALIDATION",
        "category": "ROUTING",
        "description": "Valida rutas BGP entrantes contra bases RPKI (ROA) y aplica filtros para descartar orígenes Inválidos.",
        "ros_command_template": (
            "/routing rpki add address={{ rpki_server }} port={{ rpki_port }} name=rpki-validator\n"
            '/routing filter rule add chain=RPKI_IN rule="if (rpki-verify() == invalid) { reject }" comment="Drop BGP RPKI Invalid"'
        ),
        "variables_schema": [
            {"key": "rpki_server", "label": "Servidor Caché RPKI", "default_val": "10.0.0.250", "var_type": "string"},
            {"key": "rpki_port", "label": "Puerto RTR RPKI", "default_val": "8282", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "routing/rpki",
                "payload": {"name": "rpki-validator", "address": "{{ rpki_server }}", "port": "{{ rpki_port }}"},
                "cli_command": "/routing rpki add address={{ rpki_server }} port={{ rpki_port }} name=rpki-validator",
            },
            {
                "method": "PUT",
                "endpoint": "routing/filter/rule",
                "payload": {"chain": "RPKI_IN", "rule": "if (rpki-verify() == invalid) { reject }", "comment": "Drop BGP RPKI Invalid"},
                "cli_command": '/routing filter rule add chain=RPKI_IN rule="if (rpki-verify() == invalid) { reject }" comment="Drop BGP RPKI Invalid"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "ISP_CGNAT_DETERMINISTIC_OVERLOAD",
        "category": "FIREWALL",
        "description": "Implementa Carrier-Grade NAT (CGNAT) RFC 6598 (100.64.0.0/10) con mapeo hacia IPs públicas de salida.",
        "ros_command_template": (
            '/ip firewall nat add chain=srcnat src-address={{ cgnat_subnet }} out-interface={{ wan_interface }} action=src-nat to-addresses={{ public_ip_pool }} comment="CGNAT RFC 6598 Carrier Grade NAT"'
        ),
        "variables_schema": [
            {"key": "cgnat_subnet", "label": "Subred de Clientes CGNAT", "default_val": "100.64.0.0/10", "var_type": "string"},
            {"key": "public_ip_pool", "label": "Rango/IPs Públicas Pool NAT", "default_val": "203.0.113.1-203.0.113.8", "var_type": "string"},
            {"key": "wan_interface", "label": "Interfaz de Salida WAN", "default_val": "ether1", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "ip/firewall/nat",
                "payload": {
                    "chain": "srcnat",
                    "src-address": "{{ cgnat_subnet }}",
                    "out-interface": "{{ wan_interface }}",
                    "action": "src-nat",
                    "to-addresses": "{{ public_ip_pool }}",
                    "comment": "CGNAT RFC 6598 Carrier Grade NAT",
                },
                "cli_command": '/ip firewall nat add chain=srcnat src-address={{ cgnat_subnet }} out-interface={{ wan_interface }} action=src-nat to-addresses={{ public_ip_pool }} comment="CGNAT RFC 6598 Carrier Grade NAT"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "ISP_IPV6_DUAL_STACK_PD",
        "category": "NETWORK",
        "description": "Configura cliente DHCPv6 con delegación de prefijo (PD) y asignación a bridge LAN corporativo.",
        "ros_command_template": (
            '/ipv6 dhcp-client add interface={{ wan_interface }} pool-name={{ pool_name }} pool-prefix-length=64 request=prefix comment="DHCPv6 PD Client"\n'
            '/ipv6 address add from-pool={{ pool_name }} interface={{ lan_interface }} advertise=yes comment="IPv6 LAN SLAAC / PD"'
        ),
        "variables_schema": [
            {"key": "wan_interface", "label": "Interfaz WAN DHCPv6", "default_val": "ether1", "var_type": "string"},
            {"key": "lan_interface", "label": "Interfaz LAN para IPv6", "default_val": "bridge", "var_type": "string"},
            {"key": "pool_name", "label": "Nombre del Pool Delegado", "default_val": "ipv6-pd-pool", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "ipv6/dhcp-client",
                "payload": {
                    "interface": "{{ wan_interface }}",
                    "pool-name": "{{ pool_name }}",
                    "pool-prefix-length": "64",
                    "request": "prefix",
                    "comment": "DHCPv6 PD Client",
                },
                "cli_command": '/ipv6 dhcp-client add interface={{ wan_interface }} pool-name={{ pool_name }} pool-prefix-length=64 request=prefix comment="DHCPv6 PD Client"',
            },
            {
                "method": "PUT",
                "endpoint": "ipv6/address",
                "payload": {
                    "from-pool": "{{ pool_name }}",
                    "interface": "{{ lan_interface }}",
                    "advertise": "yes",
                    "comment": "IPv6 LAN SLAAC / PD",
                },
                "cli_command": '/ipv6 address add from-pool={{ pool_name }} interface={{ lan_interface }} advertise=yes comment="IPv6 LAN SLAAC / PD"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "COPP_CONTROL_PLANE_PROTECTION",
        "category": "SECURITY",
        "description": "Control Plane Policing: Protección integral de la CPU de RouterOS frente a inundaciones y ataques de denegación de servicio.",
        "ros_command_template": (
            '/ip firewall filter add chain=input protocol=icmp limit={{ icmp_rate_limit }},5:packet action=accept comment="CoPP: Limit ICMP to CPU"\n'
            '/ip firewall filter add chain=input protocol=icmp action=drop comment="CoPP: Drop excess ICMP"\n'
            '/ip firewall filter add chain=input protocol=tcp dst-port=22,8291 connection-state=new limit={{ ssh_syn_limit }},5:packet action=accept comment="CoPP: Limit Management SYNs"'
        ),
        "variables_schema": [
            {"key": "icmp_rate_limit", "label": "Límite paquetes ICMP/s", "default_val": "50", "var_type": "string"},
            {"key": "ssh_syn_limit", "label": "Límite conexiones SSH/Winbox", "default_val": "10/min", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "ip/firewall/filter",
                "payload": {
                    "chain": "input",
                    "protocol": "icmp",
                    "limit": "{{ icmp_rate_limit }},5:packet",
                    "action": "accept",
                    "comment": "CoPP: Limit ICMP to CPU",
                },
                "cli_command": '/ip firewall filter add chain=input protocol=icmp limit={{ icmp_rate_limit }},5:packet action=accept comment="CoPP: Limit ICMP to CPU"',
            },
            {
                "method": "PUT",
                "endpoint": "ip/firewall/filter",
                "payload": {
                    "chain": "input",
                    "protocol": "icmp",
                    "action": "drop",
                    "comment": "CoPP: Drop excess ICMP",
                },
                "cli_command": '/ip firewall filter add chain=input protocol=icmp action=drop comment="CoPP: Drop excess ICMP"',
            },
            {
                "method": "PUT",
                "endpoint": "ip/firewall/filter",
                "payload": {
                    "chain": "input",
                    "protocol": "tcp",
                    "dst-port": "22,8291",
                    "connection-state": "new",
                    "limit": "{{ ssh_syn_limit }},5:packet",
                    "action": "accept",
                    "comment": "CoPP: Limit Management SYNs",
                },
                "cli_command": '/ip firewall filter add chain=input protocol=tcp dst-port=22,8291 connection-state=new limit={{ ssh_syn_limit }},5:packet action=accept comment="CoPP: Limit Management SYNs"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "BCP38_ANTI_SPOOFING_FILTER",
        "category": "SECURITY",
        "description": "Aplica filtrado estricto contra IP Source Address Spoofing (BCP 38 / RFC 2827) en interfaces perimetrales y clientes.",
        "ros_command_template": (
            '/ip firewall filter add chain=forward in-interface={{ customer_interface }} src-address={{ allowed_customer_prefixes }} action=accept comment="BCP 38: Accept valid customer prefixes"\n'
            '/ip firewall filter add chain=forward in-interface={{ customer_interface }} action=drop comment="BCP 38: Drop spoofed customer traffic"'
        ),
        "variables_schema": [
            {"key": "allowed_customer_prefixes", "label": "Prefijos Autorizados del Cliente", "default_val": "198.51.100.0/24,203.0.113.0/24", "var_type": "string"},
            {"key": "customer_interface", "label": "Interfaz del Cliente / Enlace", "default_val": "ether2", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "ip/firewall/filter",
                "payload": {
                    "chain": "forward",
                    "in-interface": "{{ customer_interface }}",
                    "src-address": "{{ allowed_customer_prefixes }}",
                    "action": "accept",
                    "comment": "BCP 38: Accept valid customer prefixes",
                },
                "cli_command": '/ip firewall filter add chain=forward in-interface={{ customer_interface }} src-address={{ allowed_customer_prefixes }} action=accept comment="BCP 38: Accept valid customer prefixes"',
            },
            {
                "method": "PUT",
                "endpoint": "ip/firewall/filter",
                "payload": {
                    "chain": "forward",
                    "in-interface": "{{ customer_interface }}",
                    "action": "drop",
                    "comment": "BCP 38: Drop spoofed customer traffic",
                },
                "cli_command": '/ip firewall filter add chain=forward in-interface={{ customer_interface }} action=drop comment="BCP 38: Drop spoofed customer traffic"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "TCP_MSS_CLAMPING_OPTIMIZER",
        "category": "NETWORK",
        "description": "Ajusta automáticamente el MSS en paquetes TCP SYN para evitar fragmentación excesiva en enlaces PPPoE o túneles VPN.",
        "ros_command_template": (
            '/ip firewall mangle add chain=forward protocol=tcp tcp-flags=syn out-interface={{ wan_interface }} action=change-mss new-mss={{ tcp_mss_ipv4 }} passthrough=yes comment="Clamp TCP MSS WAN Out"\n'
            '/ip firewall mangle add chain=forward protocol=tcp tcp-flags=syn in-interface={{ wan_interface }} action=change-mss new-mss={{ tcp_mss_ipv4 }} passthrough=yes comment="Clamp TCP MSS WAN In"'
        ),
        "variables_schema": [
            {"key": "wan_interface", "label": "Interfaz WAN / PPPoE / VPN", "default_val": "all-ppp", "var_type": "string"},
            {"key": "tcp_mss_ipv4", "label": "Valor MSS TCP", "default_val": "1452", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "ip/firewall/mangle",
                "payload": {
                    "chain": "forward",
                    "protocol": "tcp",
                    "tcp-flags": "syn",
                    "out-interface": "{{ wan_interface }}",
                    "action": "change-mss",
                    "new-mss": "{{ tcp_mss_ipv4 }}",
                    "passthrough": "yes",
                    "comment": "Clamp TCP MSS WAN Out",
                },
                "cli_command": '/ip firewall mangle add chain=forward protocol=tcp tcp-flags=syn out-interface={{ wan_interface }} action=change-mss new-mss={{ tcp_mss_ipv4 }} passthrough=yes comment="Clamp TCP MSS WAN Out"',
            },
            {
                "method": "PUT",
                "endpoint": "ip/firewall/mangle",
                "payload": {
                    "chain": "forward",
                    "protocol": "tcp",
                    "tcp-flags": "syn",
                    "in-interface": "{{ wan_interface }}",
                    "action": "change-mss",
                    "new-mss": "{{ tcp_mss_ipv4 }}",
                    "passthrough": "yes",
                    "comment": "Clamp TCP MSS WAN In",
                },
                "cli_command": '/ip firewall mangle add chain=forward protocol=tcp tcp-flags=syn in-interface={{ wan_interface }} action=change-mss new-mss={{ tcp_mss_ipv4 }} passthrough=yes comment="Clamp TCP MSS WAN In"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "ENTERPRISE_BRIDGE_VLAN_TRUNK_ACCESS",
        "category": "NETWORK",
        "description": "Configuración estandarizada de Bridge con filtrado VLAN 802.1Q, separando Trunk (uplink) de puertos Access de usuario.",
        "ros_command_template": (
            "/interface bridge port add bridge={{ bridge_name }} interface={{ access_interface }} pvid={{ access_vlan_id }}\n"
            "/interface bridge vlan add bridge={{ bridge_name }} vlan-ids={{ access_vlan_id }} tagged={{ trunk_interface }} untagged={{ access_interface }}\n"
            "/interface bridge set {{ bridge_name }} vlan-filtering=yes"
        ),
        "variables_schema": [
            {"key": "bridge_name", "label": "Nombre del Bridge", "default_val": "bridge", "var_type": "string"},
            {"key": "trunk_interface", "label": "Interfaz Trunk (Uplink)", "default_val": "sfp-sfpplus1", "var_type": "string"},
            {"key": "access_interface", "label": "Puerto Access de Usuario", "default_val": "ether2", "var_type": "string"},
            {"key": "access_vlan_id", "label": "VLAN ID Acceso", "default_val": "10", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "interface/bridge/port",
                "payload": {
                    "bridge": "{{ bridge_name }}",
                    "interface": "{{ access_interface }}",
                    "pvid": "{{ access_vlan_id }}",
                },
                "cli_command": "/interface bridge port add bridge={{ bridge_name }} interface={{ access_interface }} pvid={{ access_vlan_id }}",
            },
            {
                "method": "PUT",
                "endpoint": "interface/bridge/vlan",
                "payload": {
                    "bridge": "{{ bridge_name }}",
                    "vlan-ids": "{{ access_vlan_id }}",
                    "tagged": "{{ trunk_interface }}",
                    "untagged": "{{ access_interface }}",
                },
                "cli_command": "/interface bridge vlan add bridge={{ bridge_name }} vlan-ids={{ access_vlan_id }} tagged={{ trunk_interface }} untagged={{ access_interface }}",
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "QOS_CAKE_SMART_QUEUE",
        "category": "NETWORK",
        "description": "Erradicación de Bufferbloat mediante colas inteligentes CAKE (Common Applications Kept Enhanced) con aislamiento de flujos.",
        "ros_command_template": (
            "/queue type add name=cake-rosgrid kind=cake cake-bandwidth=0 cake-nat=yes\n"
            '/queue simple add name=cake-qos-traffic target={{ target_interface }} max-limit={{ upload_rate }}/{{ download_rate }} queue=cake-rosgrid/cake-rosgrid comment="CAKE Anti-Bufferbloat"'
        ),
        "variables_schema": [
            {"key": "target_interface", "label": "Interfaz o Target Subred", "default_val": "ether1", "var_type": "string"},
            {"key": "download_rate", "label": "Ancho de Banda Bajada (Download)", "default_val": "100M", "var_type": "string"},
            {"key": "upload_rate", "label": "Ancho de Banda Subida (Upload)", "default_val": "50M", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "queue/type",
                "payload": {
                    "name": "cake-rosgrid",
                    "kind": "cake",
                    "cake-bandwidth": "0",
                    "cake-nat": "yes",
                },
                "cli_command": "/queue type add name=cake-rosgrid kind=cake cake-bandwidth=0 cake-nat=yes",
            },
            {
                "method": "PUT",
                "endpoint": "queue/simple",
                "payload": {
                    "name": "cake-qos-traffic",
                    "target": "{{ target_interface }}",
                    "max-limit": "{{ upload_rate }}/{{ download_rate }}",
                    "queue": "cake-rosgrid/cake-rosgrid",
                    "comment": "CAKE Anti-Bufferbloat",
                },
                "cli_command": '/queue simple add name=cake-qos-traffic target={{ target_interface }} max-limit={{ upload_rate }}/{{ download_rate }} queue=cake-rosgrid/cake-rosgrid comment="CAKE Anti-Bufferbloat"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "SDWAN_WIREGUARD_SITE_TO_SITE",
        "category": "VPN",
        "description": "Túnel VPN WireGuard punto a punto de alto rendimiento cifrado con ChaCha20-Poly1305 para sucursales corporativas.",
        "ros_command_template": (
            "/interface wireguard add name={{ wg_interface }} listen-port={{ listen_port }}\n"
            "/interface wireguard peers add interface={{ wg_interface }} public-key={{ peer_public_key }} endpoint-address={{ peer_endpoint }} endpoint-port={{ peer_endpoint_port }} allowed-address={{ allowed_ips }} persistent-keepalive=25s"
        ),
        "variables_schema": [
            {"key": "wg_interface", "label": "Nombre Interfaz WireGuard", "default_val": "wg-sdwan0", "var_type": "string"},
            {"key": "listen_port", "label": "Puerto de Escucha UDP", "default_val": "13231", "var_type": "string"},
            {"key": "peer_public_key", "label": "Clave Pública del Peer Remoto", "default_val": "PEER_PUBLIC_KEY_BASE64_HERE", "var_type": "string"},
            {"key": "peer_endpoint", "label": "IP o Hostname del Peer Remoto", "default_val": "198.51.100.1", "var_type": "string"},
            {"key": "peer_endpoint_port", "label": "Puerto UDP del Peer Remoto", "default_val": "13231", "var_type": "string"},
            {"key": "allowed_ips", "label": "Subredes Remotas Autorizadas (Allowed IPs)", "default_val": "10.100.0.0/24", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "interface/wireguard",
                "payload": {"name": "{{ wg_interface }}", "listen-port": "{{ listen_port }}"},
                "cli_command": "/interface wireguard add name={{ wg_interface }} listen-port={{ listen_port }}",
            },
            {
                "method": "PUT",
                "endpoint": "interface/wireguard/peers",
                "payload": {
                    "interface": "{{ wg_interface }}",
                    "public-key": "{{ peer_public_key }}",
                    "endpoint-address": "{{ peer_endpoint }}",
                    "endpoint-port": "{{ peer_endpoint_port }}",
                    "allowed-address": "{{ allowed_ips }}",
                    "persistent-keepalive": "25s",
                },
                "cli_command": "/interface wireguard peers add interface={{ wg_interface }} public-key={{ peer_public_key }} endpoint-address={{ peer_endpoint }} endpoint-port={{ peer_endpoint_port }} allowed-address={{ allowed_ips }} persistent-keepalive=25s",
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "NIGHTLY_ENCRYPTED_BACKUP_SFTP",
        "category": "MAINTENANCE",
        "description": "Crea tarea programada nocturna para generar backup binario cifrado con AES-SHA256 en RouterOS v7.",
        "ros_command_template": (
            '/system scheduler add name=nightly-encrypted-backup start-time={{ schedule_time }} interval=1d on-event="/system backup save encryption=aes-sha256 name=nightly-rosgrid-backup password={{ backup_password }}" comment="Nightly Encrypted Backup"'
        ),
        "variables_schema": [
            {"key": "schedule_time", "label": "Hora de Ejecución Diaria", "default_val": "03:00:00", "var_type": "string"},
            {"key": "backup_password", "label": "Contraseña de Cifrado AES", "default_val": "ClaveRobustaCifradoRespaldo2026", "var_type": "string"},
        ],
        "rest_steps_template": [
            {
                "method": "PUT",
                "endpoint": "system/scheduler",
                "payload": {
                    "name": "nightly-encrypted-backup",
                    "start-time": "{{ schedule_time }}",
                    "interval": "1d",
                    "on-event": "/system backup save encryption=aes-sha256 name=nightly-rosgrid-backup password={{ backup_password }}",
                    "comment": "Nightly Encrypted Backup",
                },
                "cli_command": '/system scheduler add name=nightly-encrypted-backup start-time={{ schedule_time }} interval=1d on-event="/system backup save encryption=aes-sha256 name=nightly-rosgrid-backup password={{ backup_password }}" comment="Nightly Encrypted Backup"',
            },
        ],
        "requires_safemode": True,
    },
    {
        "name": "ACTUALIZACION_ROUTEROS_Y_FIRMWARE",
        "category": "SYSTEM",
        "description": (
            "Actualiza RouterOS v7 en el canal seleccionado y actualiza el Firmware RouterBOOT "
            "en equipos físicos (si detecta CHR, actualiza únicamente el Sistema Operativo)."
        ),
        "ros_command_template": (
            "/system package update set channel={{ update_channel }}\n"
            "/system package update check-for-updates\n"
            "# En equipos físicos RouterBOARD (omitido automáticamente en CHR):\n"
            "/system routerboard settings set auto-upgrade={{ upgrade_firmware }}\n"
            "/system routerboard upgrade\n"
            "/system package update install"
        ),
        "variables_schema": [
            {
                "key": "update_channel",
                "label": "Canal de Actualización (stable, long-term, testing, development)",
                "default_val": "stable",
                "var_type": "select",
                "options": ["stable", "long-term", "testing", "development"],
            },
            {
                "key": "upgrade_firmware",
                "label": "Actualizar Firmware RouterBOOT (auto-omitido en CHR)",
                "default_val": "yes",
                "var_type": "select",
                "options": ["yes", "no"],
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "system/package/update/set",
                "payload": {"channel": "{{ update_channel }}"},
                "cli_command": "/system package update set channel={{ update_channel }}",
            },
            {
                "method": "POST",
                "endpoint": "system/package/update/check-for-updates",
                "payload": {},
                "cli_command": "/system package update check-for-updates",
            },
            {
                "method": "POST",
                "endpoint": "system/routerboard/settings/set",
                "payload": {"auto-upgrade": "{{ upgrade_firmware }}"},
                "cli_command": "/system routerboard settings set auto-upgrade={{ upgrade_firmware }}",
            },
            {
                "method": "POST",
                "endpoint": "system/routerboard/upgrade",
                "payload": {},
                "cli_command": "/system routerboard upgrade",
            },
            {
                "method": "POST",
                "endpoint": "system/package/update/install",
                "payload": {},
                "cli_command": "/system package update install",
            },
        ],
        "requires_safemode": False,
    },
    {
        "name": "SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82",
        "category": "SECURITY",
        "description": (
            "Activa DHCP Snooping y DHCP Option 82 en el bridge especificado y configura "
            "el puerto troncal (Uplink) como Trusted para prevenir servidores Rogue DHCP en la LAN."
        ),
        "ros_command_template": (
            "/interface bridge port set [find where bridge={{ bridge_name }} and interface={{ trusted_uplink_port }}] trusted=yes\n"
            "/interface bridge set [find where name={{ bridge_name }}] dhcp-snooping=yes add-dhcp-option82={{ add_option82 }}"
        ),
        "variables_schema": [
            {
                "key": "bridge_name",
                "label": "Nombre del Bridge Objetivo",
                "default_val": "bridge1",
            },
            {
                "key": "trusted_uplink_port",
                "label": "Puerto Troncal Confiable (Trusted / Uplink hacia DHCP Server)",
                "default_val": "ether1",
            },
            {
                "key": "add_option82",
                "label": "Inyectar DHCP Option 82 (yes / no)",
                "default_val": "yes",
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "interface/bridge/port/set",
                "payload": {
                    "numbers": "{{ trusted_uplink_port }}",
                    "trusted": "yes",
                },
                "cli_command": "/interface bridge port set {{ trusted_uplink_port }} trusted=yes",
            },
            {
                "method": "POST",
                "endpoint": "interface/bridge/set",
                "payload": {
                    "numbers": "{{ bridge_name }}",
                    "dhcp-snooping": "yes",
                    "add-dhcp-option82": "{{ add_option82 }}",
                },
                "cli_command": "/interface bridge set {{ bridge_name }} dhcp-snooping=yes add-dhcp-option82={{ add_option82 }}",
            },
        ],
        "requires_safemode": True,
    },
    # 17. Huso Horario del Sistema (/system/clock)
    {
        "name": "HUSO_HORARIO_SISTEMA",
        "category": "SYSTEM",
        "description": (
            "Configura el huso horario oficial IANA del sistema (/system/clock) en toda la flota "
            "MikroTik RouterOS v7 y ajusta la autodetección por IP Cloud (time-zone-autodetect) "
            "para garantizar marcas de tiempo exactas en Syslog y auditoría WORM."
        ),
        "ros_command_template": (
            "/system clock set time-zone-autodetect={{ time_zone_autodetect }} "
            "time-zone-name={{ time_zone_name }}"
        ),
        "variables_schema": [
            {
                "key": "time_zone_name",
                "label": "Huso Horario IANA (time-zone-name)",
                "default_val": "America/Caracas",
                "required": True,
                "var_type": "select",
                "options": [
                    "America/Caracas",
                    "America/Bogota",
                    "America/Lima",
                    "America/Guayaquil",
                    "America/La_Paz",
                    "America/Santiago",
                    "America/Argentina/Buenos_Aires",
                    "America/Asuncion",
                    "America/Montevideo",
                    "America/Sao_Paulo",
                    "America/Panama",
                    "America/Costa_Rica",
                    "America/Guatemala",
                    "America/Santo_Domingo",
                    "America/Mexico_City",
                    "America/New_York",
                    "America/Chicago",
                    "America/Los_Angeles",
                    "Europe/Madrid",
                    "UTC",
                ],
            },
            {
                "key": "time_zone_autodetect",
                "label": "Autodetección de Zona Horaria por Cloud (yes / no)",
                "default_val": "no",
                "required": True,
                "var_type": "select",
                "options": ["no", "yes"],
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "system/clock/set",
                "payload": {
                    "time-zone-autodetect": "{{ time_zone_autodetect }}",
                    "time-zone-name": "{{ time_zone_name }}",
                },
                "cli_command": (
                    "/system clock set time-zone-autodetect={{ time_zone_autodetect }} "
                    "time-zone-name={{ time_zone_name }}"
                ),
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

    existing_names = {t.name for t in templates}
    missing_starters = [s for s in _DEFAULT_STARTER_TEMPLATES if s["name"] not in existing_names]
    if missing_starters:
        for starter in missing_starters:
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


async def _execute_single_step(
    client: MikrotikRestClient,
    step: dict[str, Any] | str,
    endpoint: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    """Ejecuta un paso individual REST tolerando endpoints singulares e idempotencia en RouterOS v7."""
    if isinstance(step, dict):
        method = step.get("method", "PATCH").upper()
        target_endpoint = step.get("endpoint", "").strip("/")
        body_payload = step.get("payload", {})
    else:
        method = str(step).upper()
        target_endpoint = str(endpoint or "").strip("/")
        body_payload = payload or {}

    endpoint = target_endpoint
    payload = body_payload

    # Auto-redirección de endpoints singulares que no admiten PATCH en RouterOS v7
    singleton_menus = (
        "snmp",
        "system/clock",
        "system/ntp/client",
        "system/package/update",
        "system/routerboard/settings",
        "ip/dns",
        "tool/mac-server",
        "tool/mac-server/mac-winbox",
        "tool/mac-server/ping",
        "tool/bandwidth-server",
        "tool/romon",
        "ip/ssh",
        "ip/settings",
        "ip/neighbor/discovery-settings",
        "ip/proxy",
        "ip/socks",
    )
    if (endpoint in singleton_menus or endpoint.endswith("/set")) and method in ("PATCH", "POST"):
        set_endpoint = endpoint if endpoint.endswith("/set") else f"{endpoint}/set"
        return await client.post(set_endpoint, payload)

    if method == "PUT":
        # Idempotencia preventiva para /system/logging: no duplicar reglas con misma acción y tópicos
        if endpoint == "system/logging":
            tgt_act = payload.get("action", "")
            tgt_top = payload.get("topics", "")
            tgt_set = {t.strip() for t in tgt_top.split(",") if t.strip()}
            try:
                existing_rules = await client.get("system/logging")
                if isinstance(existing_rules, list):
                    for r in existing_rules:
                        if r.get("action") == tgt_act:
                            r_top = r.get("topics", "")
                            r_set = {t.strip() for t in r_top.split(",") if t.strip()}
                            if r_set == tgt_set:
                                logger.info(
                                    "Regla de logging con tópicos '%s' y acción '%s' ya existe (idempotente)",
                                    tgt_top,
                                    tgt_act,
                                )
                                return r
            except Exception as e_log:
                logger.debug("Fallo al consultar reglas previas de logging: %s", e_log)

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
            if "already exists" in err_msg and endpoint in ("queue/type", "routing/rpki", "system/scheduler", "interface/wireguard"):
                logger.info("Recurso en %s ya existe en router, tratando como idempotente", endpoint)
                return []
            raise
    elif method == "POST":
        if endpoint == "system/package/update/install":
            try:
                return await client.post(endpoint, payload, timeout=180.0)
            except (MikrotikConnectionError, MikrotikTimeoutError):
                return {"status": "REBOOTING_FOR_UPGRADE"}
        if endpoint == "system/package/update/check-for-updates":
            await _cleanup_corrupted_npk_downloads(client)
            return await client.post(endpoint, payload, timeout=30.0)
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


async def _run_router_template_steps(
    client: MikrotikRestClient,
    router_obj: Router,
    rendered_steps: list[dict[str, Any]],
    vars_dict: dict[str, Any],
) -> dict[str, Any]:
    """Ejecuta los pasos de una plantilla omitiendo comandos RouterBOOT si el equipo es CHR."""
    is_chr = _is_chr_router(router_obj)
    executed = 0
    skipped_chr = 0
    channel = str(vars_dict.get("update_channel") or "stable").strip()
    step_log_keys: dict[str, Any] = {}
    for step in rendered_steps:
        if _should_skip_step_for_router(step, is_chr, vars_dict):
            skipped_chr += 1
            continue
        res = await _execute_single_step(client, step)
        ep = str(step.get("endpoint", "")).strip("/").lower()
        if ep == "system/package/update/install" and "error" in _extract_update_status_text(res).lower():
            await _install_routeros_via_fetch_fallback(client, router_obj, channel)
        executed += 1
        m = str(step.get("method", "POST")).upper()
        step_ep = str(step.get("endpoint", "")).strip("/")
        step_log_keys[f"{m} /rest/{step_ep} -> OK"] = True
    msg = f"Aplicados {executed} pasos con éxito"
    if is_chr and skipped_chr > 0:
        msg += f" (CHR detectado: omitidos {skipped_chr} pasos de firmware RouterBOOT; actualizado solo OS)"
    ret: dict[str, Any] = {
        "message": msg,
        "is_chr": is_chr,
        "executed_steps": executed,
        "skipped_steps": skipped_chr,
        **step_log_keys,
    }
    return ret


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
            summary = await _run_router_template_steps(client, router_obj, rendered_steps, vars_dict)

            item.status = "SUCCESS"
            item.response_summary = summary
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

    if is_l2 and approval_req_id is not None:
        from src.api.v1.webfig_common import publish_maker_checker_event

        await publish_maker_checker_event(
            tenant_id=tenant_id,
            event_name="MAKER_CHECKER_REQUESTED",
            approval_id=approval_req_id,
            summary=f"Acción masiva: {payload.title} sobre {len(target_ids)} routers",
        )

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

        effective_display = (
            f"{r.display_name} ({r.ros_identity})"
            if r.ros_identity and r.ros_identity != r.display_name
            else r.display_name
        )
        statuses.append(
            RosUpdateRouterStatus(
                router_id=r.id,
                display_name=effective_display,
                board_name=r.board_name,
                is_chr=_is_chr_router(r),
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


async def _probe_routerboard_safe(
    client: MikrotikRestClient,
    r_obj: Router,
    is_chr: bool,
    cur_fw: str | None,
    upg_fw: str | None,
) -> tuple[bool, str | None, str | None]:
    """Consulta /system/routerboard solo si no es CHR, aislando errores HTTP 400 en equipos virtuales."""
    if is_chr:
        return True, None, None
    try:
        rb_data = await client.get("system/routerboard")
        if isinstance(rb_data, dict):
            detected_chr = _is_chr_router(r_obj, rb_data)
            if not detected_chr:
                cur_fw = rb_data.get("current-firmware", cur_fw)
                upg_fw = rb_data.get("upgrade-firmware", upg_fw)
                r_obj.firmware_version = cur_fw
                r_obj.upgrade_firmware_version = upg_fw
            return detected_chr, (None if detected_chr else cur_fw), (None if detected_chr else upg_fw)
    except Exception as exc:
        if "routerboard" in str(exc).lower():
            return True, None, None
    return is_chr, cur_fw, upg_fw


async def _resolve_package_update_versions(
    client: MikrotikRestClient,
    r_obj: Router,
    channel: str,
    installed_ver: str | None,
    latest_ver: str | None,
) -> tuple[str | None, str | None, str]:
    """Obtiene installed-version, latest-version y status aplicando fallback ante bug HTTP de RouterOS 7.25."""
    await _cleanup_corrupted_npk_downloads(client)
    await client.post("system/package/update/set", {"channel": channel})
    chk_res = await client.post("system/package/update/check-for-updates", {}, timeout=30.0)
    pkg_data = await client.get("system/package/update")
    status_text = _extract_update_status_text(pkg_data) or _extract_update_status_text(chk_res) or "Checked"
    if isinstance(pkg_data, dict):
        installed_ver = str(pkg_data.get("installed-version") or installed_ver or "")
        latest_ver = str(pkg_data.get("latest-version") or latest_ver or installed_ver or "")

    if "error" in status_text.lower():
        fb_ver = await _fetch_latest_version_via_http_fallback(client, channel)
        if fb_ver:
            latest_ver = fb_ver
            clean_inst = _clean_version_token(installed_ver)
            status_text = (
                "New version is available (HTTP fallback)"
                if fb_ver != clean_inst
                else "System is already up to date"
            )
    if installed_ver:
        r_obj.ros_version = installed_ver
    if latest_ver:
        r_obj.update_available_version = latest_ver
    return installed_ver, latest_ver, status_text


async def _probe_single_router_update(
    r_obj: Router,
    channel: str,
    tenant_id: uuid.UUID,
) -> RosUpdateChannelCheckItem:
    """Configura el canal y consulta en vivo la versión disponible en MikroTik y estado CHR/RouterBOARD."""
    is_chr = _is_chr_router(r_obj)
    installed_ver = r_obj.ros_version
    latest_ver = r_obj.update_available_version or r_obj.ros_version
    status_text = "Cached inventory state"
    cur_fw = None if is_chr else r_obj.firmware_version
    upg_fw = None if is_chr else r_obj.upgrade_firmware_version

    if r_obj.vault:
        client = _create_client_from_vault(r_obj, tenant_id)
        try:
            installed_ver, latest_ver, status_text = await _resolve_package_update_versions(
                client, r_obj, channel, installed_ver, latest_ver
            )
            is_chr, cur_fw, upg_fw = await _probe_routerboard_safe(
                client, r_obj, is_chr, cur_fw, upg_fw
            )
        except Exception as exc:
            logger.warning("Fallo al sondear canal %s en %s: %s", channel, r_obj.display_name, exc)
            status_text = f"Offline / Cache ({installed_ver or 'v7'})"
        finally:
            await client.close()

    clean_inst = _clean_version_token(installed_ver)
    clean_lat = _clean_version_token(latest_ver)
    has_upd = bool(clean_lat and clean_lat != clean_inst)
    plan = "CHR_OS_ONLY" if is_chr else "ROUTERBOARD_OS_AND_FIRMWARE"
    effective_display = (
        f"{r_obj.display_name} ({r_obj.ros_identity})"
        if r_obj.ros_identity and r_obj.ros_identity != r_obj.display_name
        else r_obj.display_name
    )
    return RosUpdateChannelCheckItem(
        router_id=r_obj.id,
        display_name=effective_display,
        board_name=r_obj.board_name,
        is_chr=is_chr,
        channel=channel,
        installed_version=installed_ver,
        latest_version=latest_ver,
        update_available=has_upd,
        status_text=status_text,
        current_firmware=cur_fw,
        upgrade_firmware=upg_fw,
        action_plan=plan,
    )


@router.post("/ros-updates/check", response_model=RosUpdateChannelCheckResponse)
async def check_fleet_updates_by_channel(
    payload: RosUpdateChannelCheckRequest,
    claims: dict[str, Any] = Depends(require_roles(*_OPERATOR_ROLES)),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RosUpdateChannelCheckResponse:
    """Selecciona el canal de actualización y consulta la versión disponible en la flota."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = select(Router).options(selectinload(Router.vault)).where(Router.tenant_id == tenant_id)
    if payload.router_ids:
        stmt = stmt.where(Router.id.in_(payload.router_ids))
    stmt = stmt.order_by(Router.display_name)
    routers = list((await db.execute(stmt)).scalars().all())

    items: list[RosUpdateChannelCheckItem] = []
    for r_obj in routers:
        item = await _probe_single_router_update(r_obj, payload.channel, tenant_id)
        items.append(item)

    await db.commit()
    avail_cnt = sum(1 for i in items if i.update_available)
    chr_cnt = sum(1 for i in items if i.is_chr)
    rb_cnt = len(items) - chr_cnt
    return RosUpdateChannelCheckResponse(
        channel=payload.channel,
        checked_count=len(items),
        updates_available_count=avail_cnt,
        chr_count=chr_cnt,
        routerboard_count=rb_cnt,
        items=items,
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


async def _trigger_router_package_install(
    client: MikrotikRestClient,
    r_obj: Router,
    channel: str,
    chk_res: Any,
) -> Any:
    """Dispara system/package/update/install con timeout extendido o aplica fallback /tool/fetch si hay error HTTP."""
    chk_status = _extract_update_status_text(chk_res)
    if "error" in chk_status.lower():
        return await _install_routeros_via_fetch_fallback(client, r_obj, channel)

    try:
        update_res = await client.post("system/package/update/install", {}, timeout=180.0)
    except (MikrotikConnectionError, MikrotikTimeoutError) as exc:
        logger.info("Router %s cerró conexión durante install/reboot: %s", r_obj.display_name, exc)
        return {"status": "REBOOTING_FOR_UPGRADE"}

    inst_status = _extract_update_status_text(update_res)
    if "error" in inst_status.lower():
        return await _install_routeros_via_fetch_fallback(client, r_obj, channel)

    if r_obj.update_available_version:
        r_obj.ros_version = r_obj.update_available_version
    return update_res


async def _execute_single_router_upgrade(
    rid: uuid.UUID,
    payload: RosUpdateExecuteRequest,
    claims: dict[str, Any],
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    stage_idx: int,
) -> tuple[dict[str, Any], bool]:
    """Ejecuta backup e instalación para un router individual respetando auto-detección CHR."""
    try:
        r_obj, client = await get_router_and_client(rid, claims, db)
        backup_ok = await _perform_pre_upgrade_backup(client, r_obj, tenant_id, user_id, db)
        if not backup_ok:
            return {"router_id": str(rid), "status": "ABORTED_PRE_BACKUP_FAILED", "stage": stage_idx}, False

        is_chr = _is_chr_router(r_obj)
        await _cleanup_corrupted_npk_downloads(client)
        await client.post("system/package/update/set", {"channel": payload.channel})
        chk_res = await client.post("system/package/update/check-for-updates", {}, timeout=30.0)

        if payload.auto_upgrade_firmware and not is_chr:
            try:
                await client.post("system/routerboard/settings/set", {"auto-upgrade": "yes"})
                await client.post("system/routerboard/upgrade", {})
            except MikrotikApiError as rb_exc:
                if "routerboard" in str(rb_exc).lower():
                    is_chr = True
                else:
                    raise

        prev_version = _clean_version_token(r_obj.ros_version) or None
        update_res = await _trigger_router_package_install(client, r_obj, payload.channel, chk_res)
        target_ver = (
            update_res.get("target_version")
            if isinstance(update_res, dict) and update_res.get("target_version")
            else (r_obj.update_available_version or r_obj.ros_version)
        )
        mode = "CHR_OS_ONLY" if is_chr else "ROUTERBOARD_OS_AND_FIRMWARE"
        return {
            "router_id": str(rid),
            "display_name": r_obj.display_name,
            "status": "UPGRADE_TRIGGERED",
            "mode": mode,
            "is_chr": is_chr,
            "channel": payload.channel,
            "installed_version": prev_version,
            "target_version": target_ver,
            "detail": update_res,
            "stage": stage_idx,
        }, True
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
