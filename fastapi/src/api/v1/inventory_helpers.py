# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Funciones auxiliares para autodescubrimiento, enriquecimiento de telemetría y validación de inventario."""

import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from src.core.crypto import encrypt_aes_gcm
from src.mikrotik.client import MikrotikRestClient
from src.models.inventory import (
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterTag,
    SSLTrustStatusEnum,
)
from src.schemas.inventory import (
    CsvCommitRowItem,
    RouterResponse,
    UpdateRouterRequest,
    validate_router_target_url,
)

logger = logging.getLogger(__name__)


async def enrich_router_telemetry(redis: Any, tenant_id: uuid.UUID, r_id: uuid.UUID) -> dict[str, Any]:
    """Obtiene el estado de telemetría en vivo y presencia Syslog desde KeyDB."""
    key = f"rg:{tenant_id}:mon_state:{r_id}"
    syslog_active_key = f"rg:{tenant_id}:router:{r_id}:syslog:active"
    syslog_ring_key = f"rg:{tenant_id}:router:{r_id}:syslog:ring"
    syslog_conf_key = f"rg:{tenant_id}:router:{r_id}:syslog:configured"

    try:
        pipeline = redis.pipeline()
        pipeline.hgetall(key)
        pipeline.exists(syslog_active_key)
        pipeline.llen(syslog_ring_key)
        pipeline.exists(syslog_conf_key)
        res = await pipeline.execute()
        data = res[0] or {} if len(res) > 0 else {}
        syslog_has_traffic = bool(res[1]) if len(res) > 1 else False
        syslog_count = int(res[2]) if len(res) > 2 and res[2] else 0
        syslog_configured = bool(res[3]) if len(res) > 3 else False
        syslog_active = syslog_has_traffic or (syslog_count > 0) or syslog_configured
    except Exception:
        data = {}
        syslog_active = False
        syslog_count = 0

    if not data:
        return {
            "operational_status": "ONLINE" if syslog_active else "OFFLINE",
            "cpu_load_percent": None,
            "memory_used_percent": None,
            "syslog_active": syslog_active,
            "syslog_event_count": syslog_count,
        }
    op_status = data.get("operational_status") or data.get("state", "ONLINE")
    if syslog_active and op_status == "OFFLINE":
        op_status = "ONLINE"
    cpu_val = data.get("last_cpu_load_pct") or data.get("cpu")
    cpu = int(cpu_val) if cpu_val and cpu_val.isdigit() else None
    free_mem_val = data.get("last_free_memory_pct")
    ram: int | None = None
    if free_mem_val and free_mem_val.isdigit():
        ram = max(0, min(100, 100 - int(free_mem_val)))
    else:
        ram_val = data.get("ram")
        ram = int(ram_val) if ram_val and ram_val.isdigit() else None
    return {
        "operational_status": op_status,
        "cpu_load_percent": cpu,
        "memory_used_percent": ram,
        "syslog_active": syslog_active,
        "syslog_event_count": syslog_count,
    }


async def _discover_identity(client: MikrotikRestClient, r: Router) -> None:
    try:
        ident_res = await client.get("/system/identity")
        if isinstance(ident_res, dict) and "name" in ident_res:
            r.ros_identity = str(ident_res["name"])
    except Exception as exc:
        logger.debug("Discovery identity error: %s", exc)


async def _discover_resource(client: MikrotikRestClient, r: Router) -> None:
    try:
        res_data = await client.get("/system/resource")
        if isinstance(res_data, dict):
            r.ros_version = res_data.get("version", r.ros_version)
            r.board_name = res_data.get("board-name", r.board_name)
            r.architecture_name = res_data.get("architecture-name", r.architecture_name)
            if not r.model_name and r.board_name:
                r.model_name = r.board_name
    except Exception as exc:
        logger.debug("Discovery resource error: %s", exc)


async def _discover_routerboard(client: MikrotikRestClient, r: Router) -> None:
    try:
        rb_data = await client.get("/system/routerboard")
        if isinstance(rb_data, dict):
            r.model_name = rb_data.get("model", r.model_name or r.board_name)
            r.firmware_version = rb_data.get("current-firmware", r.firmware_version)
            r.upgrade_firmware_version = rb_data.get("upgrade-firmware", r.upgrade_firmware_version)
            sn = rb_data.get("serial-number")
            if sn and (not r.serial_number or r.serial_number == "UNKNOWN"):
                r.serial_number = str(sn)
    except Exception as exc:
        logger.debug("Discovery routerboard error: %s", exc)


async def discover_hardware(client: MikrotikRestClient, r: Router) -> None:
    """Descubre identidad, recursos y routerboard mediante RouterOS REST API."""
    await _discover_identity(client, r)
    await _discover_resource(client, r)
    await _discover_routerboard(client, r)


def inspect_router_syslog_config(actions: Any, rules: Any = None) -> bool:
    """Evalúa determinísticamente si RouterOS v7 tiene Syslog remoto activo hacia RoSGrid.

    Criterio Canónico (Doble Candado - Espec 43):
    1. Debe existir en /system/logging/action una acción con name == 'rosgridsyslog' y target == 'remote',
       con destino 'remote' válido (distinto de '0.0.0.0' y no vacío).
    2. Debe existir en /system/logging al menos una regla activa (disabled == false) que utilice
       la acción 'rosgridsyslog'.
    3. Las configuraciones de fábrica estándar de MikroTik (acciones 'memory', 'disk', 'echo', 'remote'
       con 0.0.0.0 y sin reglas activas de RoSGrid) retornan estrictamente False.
    """
    if not isinstance(actions, list) or not isinstance(rules, list):
        return False

    has_valid_rosgrid_action = False
    for act in actions:
        if not isinstance(act, dict):
            continue
        name = str(act.get("name", "")).strip().lower()
        target = str(act.get("target", "")).strip().lower()
        remote_dest = str(act.get("remote", "")).strip()

        # Candado 1: Acción debe llamarse estrictamente 'rosgridsyslog'
        if name == "rosgridsyslog" and target == "remote":
            if remote_dest and remote_dest != "0.0.0.0":
                has_valid_rosgrid_action = True
                break

    if not has_valid_rosgrid_action:
        return False

    # Candado 2: Debe existir regla activa apuntando a 'rosgridsyslog'
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        act_name = str(rule.get("action", "")).strip().lower()
        disabled_val = str(rule.get("disabled", "false")).strip().lower()
        is_disabled = disabled_val in ("true", "yes", "1")
        if act_name == "rosgridsyslog" and not is_disabled:
            return True

    return False


async def discover_and_persist_syslog_status(
    client: MikrotikRestClient,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    redis: Any = None,
) -> bool:
    """Consulta la configuración de Syslog en el router y actualiza el estado en KeyDB."""
    try:
        from src.redis_layer.client import get_redis_client

        r_client = redis or get_redis_client()
        actions = await client.get("/system/logging/action")
        rules = await client.get("/system/logging")
        has_syslog = inspect_router_syslog_config(actions, rules)
        syslog_conf_key = f"rg:{tenant_id}:router:{router_id}:syslog:configured"
        syslog_active_key = f"rg:{tenant_id}:router:{router_id}:syslog:active"
        if has_syslog:
            await r_client.set(syslog_conf_key, "1", ex=86400)
            await r_client.set(syslog_active_key, "1", ex=3600)
        else:
            await r_client.delete(syslog_conf_key)
            await r_client.delete(syslog_active_key)
        return has_syslog
    except Exception as exc:
        logger.debug("Error comprobando Syslog en router %s: %s", router_id, exc)
        return False


async def perform_discovery(client: MikrotikRestClient, r: Router, redis: Any = None) -> bool:
    """Verifica huella SSL TOFU y actualiza hardware del equipo."""
    try:
        fp = await client.ensure_ssl_verified()
        if fp and (r.ssl_trust_status == SSLTrustStatusEnum.PENDING_TOFU or not r.ssl_sha256_fingerprint):
            r.ssl_sha256_fingerprint = fp
            r.ssl_trust_status = SSLTrustStatusEnum.TRUSTED_PINNED
            r.ssl_pinned_at = datetime.now(UTC)

        await discover_hardware(client, r)
        await discover_and_persist_syslog_status(client, r.tenant_id, r.id, redis)
        r.is_reachable = True
        r.last_seen_at = datetime.now(UTC)
        r.last_discovery_sync_at = datetime.now(UTC)
        r.last_connection_error = None
        return True
    except Exception as exc:
        r.is_reachable = False
        r.last_connection_error = str(exc)
        logger.warning("Fallo en autodescubrimiento de %s: %s", r.display_name, exc)
        return False


def build_router_response(r: Router, telemetry: dict[str, Any]) -> RouterResponse:
    """Construye esquema de respuesta de Router combinando modelo y métricas en vivo."""
    tag_names = [t.tag_name for t in r.tags] if r.tags else []
    is_effective_reachable = bool(
        r.is_reachable
        or telemetry.get("syslog_active")
        or (telemetry.get("operational_status") == "ONLINE")
    )
    operational_status = telemetry.get("operational_status", "OFFLINE")
    if is_effective_reachable and operational_status == "OFFLINE":
        operational_status = "ONLINE"

    return RouterResponse(
        id=r.id,
        tenant_id=r.tenant_id,
        display_name=r.display_name,
        api_base_url=r.api_base_url,
        api_port=r.api_port,
        network_role=r.network_role,
        admin_state=r.admin_state,
        physical_location=r.physical_location,
        latitude=r.latitude,
        longitude=r.longitude,
        online_since_date=r.online_since_date,
        serial_number=r.serial_number,
        tags=tag_names,
        operational_notes=r.operational_notes,
        site_contact_info=r.site_contact_info,
        ros_identity=r.ros_identity,
        board_name=r.board_name,
        model_name=r.model_name,
        architecture_name=r.architecture_name,
        ros_version=r.ros_version,
        firmware_version=r.firmware_version,
        upgrade_firmware_version=r.upgrade_firmware_version,
        is_reachable=is_effective_reachable,
        last_seen_at=r.last_seen_at,
        ssl_trust_status=r.ssl_trust_status,
        ssl_sha256_fingerprint=r.ssl_sha256_fingerprint,
        ssl_pinned_at=r.ssl_pinned_at,
        operational_status=operational_status,
        cpu_load_percent=telemetry.get("cpu_load_percent"),
        memory_used_percent=telemetry.get("memory_used_percent"),
        syslog_active=telemetry.get("syslog_active", False),
        syslog_event_count=telemetry.get("syslog_event_count", 0),
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def apply_router_scalar_updates(r: Router, payload: UpdateRouterRequest) -> None:
    """Aplica de forma genérica campos escalares recibidos en actualización."""
    update_data = payload.model_dump(exclude_unset=True, exclude={"tags"})
    for field, val in update_data.items():
        if isinstance(val, str):
            setattr(r, field, val.strip())
        else:
            setattr(r, field, val)


def _check_csv_serial(sn: str, existing_serials: set[str], seen_serials: set[str], errors: list[str]) -> None:
    if not sn:
        errors.append("serial_number es obligatorio")
    elif sn in existing_serials:
        errors.append(f"El serial_number {sn} ya existe en este Tenant")
    elif sn in seen_serials:
        errors.append(f"El serial_number {sn} está duplicado en el mismo archivo")
    else:
        seen_serials.add(sn)


def validate_single_csv_row(
    row: dict[str, str],
    existing_serials: set[str],
    seen_serials: set[str],
) -> tuple[bool, list[str]]:
    """Valida una fila de importación CSV garantizando unicidad de serial y tolerando alias de plantilla."""
    errors: list[str] = []
    name = (row.get("display_name") or row.get("name") or "").strip()
    raw_url = (row.get("api_base_url") or row.get("ip_address") or row.get("ip") or "").strip()
    if raw_url and not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        raw_url = f"https://{raw_url}"
    sn = (row.get("serial_number") or row.get("serial") or "").strip()
    pwd = (row.get("api_password") or row.get("ros_password") or row.get("password") or "").strip()

    if not name:
        errors.append("display_name es obligatorio")
    if not raw_url.startswith("https://"):
        errors.append("api_base_url debe comenzar con https://")
    else:
        try:
            validate_router_target_url(raw_url)
        except ValueError as err:
            errors.append(str(err))
    _check_csv_serial(sn, existing_serials, seen_serials, errors)
    if not pwd:
        errors.append("api_password es obligatorio")
    return len(errors) == 0, errors


def row_to_commit_item(row: dict[str, str]) -> CsvCommitRowItem:
    """Convierte un diccionario de fila CSV a CsvCommitRowItem tolerando nombres alternativos."""
    name = (row.get("display_name") or row.get("name") or "").strip()
    url = (row.get("api_base_url") or row.get("ip_address") or row.get("ip") or "").strip()
    if url and not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    port_val = (row.get("api_port") or "").strip()
    port = int(port_val) if port_val and port_val.isdigit() else 443

    user = (row.get("api_username") or row.get("ros_username") or row.get("username") or "").strip()
    if not user:
        raise ValueError(
            f"Fila con display_name='{row.get('display_name', '')}' no especifica usuario (ros_username o api_username)."
        )
    pwd = (row.get("api_password") or row.get("ros_password") or row.get("password") or "").strip()

    role_str = (row.get("network_role") or "EDGE_BGP").strip().upper()
    network_role = role_str if role_str else "EDGE_BGP"

    state_str = (row.get("admin_state") or "PRODUCTION").strip().upper()
    try:
        admin_state = RouterAdminStateEnum(state_str)
    except ValueError:
        admin_state = RouterAdminStateEnum.PRODUCTION

    location = (row.get("physical_location") or row.get("location") or "Sede Central").strip()

    lat_val = (row.get("latitude") or "").strip()
    lat = Decimal(lat_val) if lat_val else None

    lon_val = (row.get("longitude") or "").strip()
    lon = Decimal(lon_val) if lon_val else None

    date_val = (row.get("online_since_date") or "").strip()
    if date_val:
        try:
            online_date = date.fromisoformat(date_val)
        except ValueError:
            online_date = date.today()
    else:
        online_date = date.today()

    sn = (row.get("serial_number") or row.get("serial") or "").strip()

    tags_raw = row.get("tags") or ""
    tags = [t.strip() for t in tags_raw.replace(";", ",").split(",") if t.strip()]

    return CsvCommitRowItem(
        display_name=name,
        api_base_url=url,
        api_port=port,
        api_username=user,
        api_password=pwd,
        network_role=network_role,
        admin_state=admin_state,
        physical_location=location,
        latitude=lat,
        longitude=lon,
        online_since_date=online_date,
        serial_number=sn,
        tags=tags,
        auto_rotate_credentials=True,
        rotation_interval_days=30,
    )


def build_router_from_csv(
    item: CsvCommitRowItem, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Router, list[RouterTag], RouterCredentialsVault]:
    """Instancia Router, Tags y Vault desde una fila CSV verificada."""
    router_id = uuid.uuid4()
    r = Router(
        id=router_id,
        tenant_id=tenant_id,
        display_name=item.display_name.strip(),
        api_base_url=item.api_base_url.strip(),
        api_port=item.api_port,
        network_role=item.network_role,
        admin_state=item.admin_state,
        physical_location=item.physical_location.strip(),
        latitude=item.latitude,
        longitude=item.longitude,
        online_since_date=item.online_since_date,
        serial_number=item.serial_number.strip(),
        created_by=user_id,
    )
    tags = [
        RouterTag(tenant_id=tenant_id, router_id=router_id, tag_name=clean_tag)
        for tag in item.tags
        if (clean_tag := tag.strip().lower())
    ]
    aad = f"{tenant_id}:{router_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(item.api_password.encode("utf-8"), aad)
    vault = RouterCredentialsVault(
        router_id=router_id,
        tenant_id=tenant_id,
        api_username=item.api_username.strip(),
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
        auto_rotate_enabled=item.auto_rotate_credentials,
        rotation_interval_days=item.rotation_interval_days,
        updated_by=user_id,
    )
    return r, tags, vault
