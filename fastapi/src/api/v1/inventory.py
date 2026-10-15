# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Inventario de Equipos MikroTik, Importación Masiva CSV y Re-Pin SSL TOFU."""

import csv
import io
import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pyotp
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import write_audit_log
from src.core.crypto import decrypt_aes_gcm, encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.mikrotik.ssl_tofu import SSLTrustStatus
from src.models.core import SystemRoleEnum, Tenant, User, UserRouterPermission
from src.models.inventory import (
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterNetworkRoleEnum,
    RouterTag,
    SSLTrustStatusEnum,
)
from src.redis_layer.client import get_redis_client
from src.schemas.inventory import (
    CreateRouterRequest,
    CsvCommitRequest,
    CsvCommitResponse,
    CsvDryRunResponse,
    CsvDryRunRowPreview,
    RePinSSLRequest,
    RouterResponse,
    UpdateRouterRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

_GLOBAL_ROUTER_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    SystemRoleEnum.TENANT_ADMIN.value,
    SystemRoleEnum.SUPERVISOR.value,
    SystemRoleEnum.INVENTORY_MANAGER.value,
    SystemRoleEnum.AUDITOR.value,
}


async def _check_tenant_router_quota(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    count_stmt = select(func.count(Router.id)).where(Router.tenant_id == tenant_id)
    current_count = (await db.execute(count_stmt)).scalar() or 0
    if current_count >= tenant.max_routers_quota:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Límite de cuota alcanzado ({tenant.max_routers_quota} routers permitidos para este Tenant)",
        )


def _apply_role_filters(
    query: Any,
    claims: dict[str, Any],
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Any:
    user_role = claims.get("rol")
    has_all = claims.get("all_r", False)
    if user_role in _GLOBAL_ROUTER_ROLES or has_all:
        return query.where(Router.tenant_id == tenant_id)

    perm_subq = (
        select(UserRouterPermission.router_id)
        .where(
            UserRouterPermission.tenant_id == tenant_id,
            UserRouterPermission.user_id == user_id,
            UserRouterPermission.can_read.is_(True),
        )
        .scalar_subquery()
    )
    return query.where(Router.tenant_id == tenant_id, Router.id.in_(perm_subq))


def _apply_query_search_filters(
    query: Any,
    network_role: RouterNetworkRoleEnum | None = None,
    admin_state: RouterAdminStateEnum | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> Any:
    if network_role:
        query = query.where(Router.network_role == network_role)
    if admin_state:
        query = query.where(Router.admin_state == admin_state)
    if tag:
        tag_subq = select(RouterTag.router_id).where(RouterTag.tag_name == tag.strip().lower()).scalar_subquery()
        query = query.where(Router.id.in_(tag_subq))
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Router.display_name.ilike(term),
                Router.serial_number.ilike(term),
                Router.ros_identity.ilike(term),
                Router.physical_location.ilike(term),
                Router.api_base_url.ilike(term),
            )
        )
    return query


async def _enrich_router_telemetry(redis: Any, tenant_id: uuid.UUID, r_id: uuid.UUID) -> dict[str, Any]:
    key = f"rg:{tenant_id}:mon_state:{r_id}"
    data = await redis.hgetall(key)
    if not data:
        return {"operational_status": "OFFLINE", "cpu_load_percent": None, "memory_used_percent": None}
    op_status = data.get("state", "ONLINE")
    cpu = int(data["cpu"]) if "cpu" in data and data["cpu"].isdigit() else None
    ram = int(data["ram"]) if "ram" in data and data["ram"].isdigit() else None
    return {"operational_status": op_status, "cpu_load_percent": cpu, "memory_used_percent": ram}


async def _discover_hardware(client: MikrotikRestClient, r: Router) -> None:
    try:
        ident_res = await client.get("/system/identity")
        if isinstance(ident_res, dict) and "name" in ident_res:
            r.ros_identity = str(ident_res["name"])
    except Exception as exc:
        logger.debug("Discovery identity error: %s", exc)

    try:
        res_data = await client.get("/system/resource")
        if isinstance(res_data, dict):
            r.ros_version = res_data.get("version", r.ros_version)
            r.board_name = res_data.get("board-name", r.board_name)
            r.architecture_name = res_data.get("architecture-name", r.architecture_name)
    except Exception as exc:
        logger.debug("Discovery resource error: %s", exc)

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


async def _perform_discovery(client: MikrotikRestClient, r: Router) -> bool:
    try:
        fp = await client.ensure_ssl_verified()
        if fp and (r.ssl_trust_status == SSLTrustStatusEnum.PENDING_TOFU or not r.ssl_sha256_fingerprint):
            r.ssl_sha256_fingerprint = fp
            r.ssl_trust_status = SSLTrustStatusEnum.TRUSTED_PINNED
            r.ssl_pinned_at = datetime.now(UTC)

        await _discover_hardware(client, r)
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


def _build_router_response(r: Router, telemetry: dict[str, Any]) -> RouterResponse:
    tag_names = [t.tag_name for t in r.tags] if r.tags else []
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
        ssl_trust_status=r.ssl_trust_status,
        ssl_sha256_fingerprint=r.ssl_sha256_fingerprint,
        is_reachable=r.is_reachable,
        last_seen_at=r.last_seen_at,
        last_discovery_sync_at=r.last_discovery_sync_at,
        operational_status=telemetry["operational_status"],
        cpu_load_percent=telemetry["cpu_load_percent"],
        memory_used_percent=telemetry["memory_used_percent"],
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/routers", response_model=list[RouterResponse])
async def list_routers(
    network_role: RouterNetworkRoleEnum | None = None,
    admin_state: RouterAdminStateEnum | None = None,
    tag: str | None = None,
    search: str | None = None,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[RouterResponse]:
    """Lista los equipos MikroTik del Tenant con filtros y enriquecimiento en vivo desde Redis."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    redis = get_redis_client()

    query = select(Router).options(selectinload(Router.tags))
    query = _apply_role_filters(query, claims, tenant_id, user_id)
    query = _apply_query_search_filters(query, network_role, admin_state, tag, search)
    query = query.order_by(Router.display_name.asc())

    result = await db.execute(query)
    routers = result.scalars().all()

    response_items = []
    for r in routers:
        telemetry = await _enrich_router_telemetry(redis, tenant_id, r.id)
        response_items.append(_build_router_response(r, telemetry))
    return response_items


@router.post("/routers", response_model=RouterResponse, status_code=status.HTTP_201_CREATED)
async def create_router(
    payload: CreateRouterRequest,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Registra un nuevo router MikroTik, almacena credenciales cifradas y realiza TOFU."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    await _check_tenant_router_quota(db, tenant_id)

    new_router = Router(
        tenant_id=tenant_id,
        display_name=payload.display_name.strip(),
        api_base_url=payload.api_base_url.strip(),
        api_port=payload.api_port,
        network_role=payload.network_role,
        admin_state=payload.admin_state,
        physical_location=payload.physical_location.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        online_since_date=payload.online_since_date,
        serial_number=payload.serial_number.strip(),
        operational_notes=payload.operational_notes,
        site_contact_info=payload.site_contact_info,
        created_by=user_id,
    )
    db.add(new_router)
    await db.flush()

    for tag_name in payload.tags:
        clean_tag = tag_name.strip().lower()
        if clean_tag:
            db.add(RouterTag(tenant_id=tenant_id, router_id=new_router.id, tag_name=clean_tag))

    aad = f"{tenant_id}:{new_router.id}".encode("utf-8")
    ct, iv, tag = encrypt_aes_gcm(payload.api_password.encode("utf-8"), aad)
    db.add(
        RouterCredentialsVault(
            router_id=new_router.id,
            tenant_id=tenant_id,
            api_username=payload.api_username.strip(),
            current_password_ciphertext=ct,
            current_password_iv=iv,
            current_password_tag=tag,
            auto_rotate_enabled=payload.auto_rotate_credentials,
            rotation_interval_days=payload.rotation_interval_days,
            updated_by=user_id,
        )
    )

    if payload.connect_and_discover_now:
        host = payload.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        async with MikrotikRestClient(
            host=host,
            port=payload.api_port,
            username=payload.api_username,
            password=payload.api_password,
            timeout=5.0,
        ) as client:
            await _perform_discovery(client, new_router)

    await db.commit()
    await db.refresh(new_router, ["tags"])

    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent")
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="INVENTORY",
        event_action="ROUTER_CREATED",
        router_id=new_router.id,
        router_display_name=new_router.display_name,
        after_state={"display_name": new_router.display_name, "serial_number": new_router.serial_number},
    )
    await db.commit()

    redis = get_redis_client()
    telemetry = await _enrich_router_telemetry(redis, tenant_id, new_router.id)
    return _build_router_response(new_router, telemetry)


@router.get("/routers/{router_id}", response_model=RouterResponse)
async def get_router(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Consulta la ficha completa de un equipo MikroTik."""
    tenant_id = uuid.UUID(claims["tid"])
    query = select(Router).options(selectinload(Router.tags)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    redis = get_redis_client()
    telemetry = await _enrich_router_telemetry(redis, tenant_id, r.id)
    return _build_router_response(r, telemetry)


@router.put("/routers/{router_id}", response_model=RouterResponse)
async def update_router(
    router_id: uuid.UUID,
    payload: UpdateRouterRequest,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Actualiza metadatos, ubicación o etiquetas de un router."""
    tenant_id = uuid.UUID(claims["tid"])
    query = select(Router).options(selectinload(Router.tags)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    if payload.display_name:
        r.display_name = payload.display_name.strip()
    if payload.api_base_url:
        r.api_base_url = payload.api_base_url.strip()
    if payload.api_port:
        r.api_port = payload.api_port
    if payload.network_role:
        r.network_role = payload.network_role
    if payload.admin_state:
        r.admin_state = payload.admin_state
    if payload.physical_location:
        r.physical_location = payload.physical_location.strip()
    if payload.latitude is not None:
        r.latitude = payload.latitude
    if payload.longitude is not None:
        r.longitude = payload.longitude
    if payload.online_since_date:
        r.online_since_date = payload.online_since_date
    if payload.serial_number:
        r.serial_number = payload.serial_number.strip()
    if payload.operational_notes is not None:
        r.operational_notes = payload.operational_notes
    if payload.site_contact_info is not None:
        r.site_contact_info = payload.site_contact_info

    if payload.tags is not None:
        await db.execute(delete(RouterTag).where(RouterTag.router_id == r.id))
        for tag_name in payload.tags:
            clean_tag = tag_name.strip().lower()
            if clean_tag:
                db.add(RouterTag(tenant_id=tenant_id, router_id=r.id, tag_name=clean_tag))

    await db.commit()
    await db.refresh(r, ["tags"])
    redis = get_redis_client()
    telemetry = await _enrich_router_telemetry(redis, tenant_id, r.id)
    return _build_router_response(r, telemetry)


@router.delete("/routers/{router_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_router(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> None:
    """Elimina permanentemente un router MikroTik del inventario."""
    tenant_id = uuid.UUID(claims["tid"])
    r = await db.get(Router, router_id)
    if not r or r.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    await db.delete(r)
    await db.commit()


@router.post("/routers/{router_id}/sync-discovery", response_model=RouterResponse)
async def sync_discovery(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Fuerza autodescubrimiento y sincronización de versión/hardware con el MikroTik."""
    tenant_id = uuid.UUID(claims["tid"])
    query = (
        select(Router)
        .options(selectinload(Router.tags), selectinload(Router.vault))
        .where(Router.id == router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(query)).scalar_one_or_none()
    if not r or not r.vault:
        raise HTTPException(status_code=404, detail="Router o credenciales no encontradas")

    aad = f"{tenant_id}:{r.id}".encode("utf-8")
    raw_pass = decrypt_aes_gcm(
        r.vault.current_password_ciphertext,
        r.vault.current_password_iv,
        r.vault.current_password_tag,
        aad,
    ).decode("utf-8")

    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    async with MikrotikRestClient(
        host=host,
        port=r.api_port,
        username=r.vault.api_username,
        password=raw_pass,
        ssl_pinned_fingerprint=r.ssl_sha256_fingerprint,
        timeout=8.0,
    ) as client:
        await _perform_discovery(client, r)

    await db.commit()
    await db.refresh(r, ["tags"])
    redis = get_redis_client()
    telemetry = await _enrich_router_telemetry(redis, tenant_id, r.id)
    return _build_router_response(r, telemetry)


@router.post("/routers/{router_id}/repin-ssl", status_code=status.HTTP_200_OK)
async def repin_ssl(
    router_id: uuid.UUID,
    payload: RePinSSLRequest,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> dict[str, Any]:
    """Autoriza un nuevo certificado SSL autofirmado (Re-Pin TOFU) tras validar 2FA TOTP."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    user = await db.get(User, user_id)
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=400, detail="El administrador no tiene 2FA TOTP configurado")

    aad_user = f"{tenant_id}:{user.id}".encode("utf-8")
    secret = decrypt_aes_gcm(
        user.totp_secret_ciphertext,
        user.totp_secret_iv,
        user.totp_secret_tag,
        aad_user,
    ).decode("utf-8")

    if not pyotp.TOTP(secret).verify(payload.totp_code, valid_window=1):
        raise HTTPException(status_code=401, detail="Código 2FA TOTP inválido o expirado")

    r = await db.get(Router, router_id)
    if not r or r.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    r.ssl_sha256_fingerprint = payload.expected_new_sha256_fingerprint.strip().lower()
    r.ssl_trust_status = SSLTrustStatusEnum.TRUSTED_PINNED
    r.ssl_pinned_at = datetime.now(UTC)

    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent")
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=user.username,
        actor_role=user.role,
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="SECURITY",
        event_action="ROUTER_SSL_REPINNED",
        router_id=r.id,
        router_display_name=r.display_name,
        after_state={"ssl_sha256_fingerprint": r.ssl_sha256_fingerprint},
    )
    await db.commit()
    return {"status": "SUCCESS", "fingerprint": r.ssl_sha256_fingerprint}


# ============================================================================
# IMPORTACIÓN MASIVA CSV
# ============================================================================


def _validate_single_csv_row(
    row: dict[str, str],
    row_num: int,
    existing_serials: set[str],
    seen_serials: set[str],
) -> tuple[bool, list[str]]:
    errors = []
    name = row.get("display_name", "").strip()
    url = row.get("api_base_url", "").strip()
    sn = row.get("serial_number", "").strip()
    pwd = row.get("api_password", "").strip()

    if not name:
        errors.append("display_name es obligatorio")
    if not url.startswith("https://"):
        errors.append("api_base_url debe comenzar con https://")
    if not sn:
        errors.append("serial_number es obligatorio")
    elif sn in existing_serials:
        errors.append(f"El serial_number {sn} ya existe en este Tenant")
    elif sn in seen_serials:
        errors.append(f"El serial_number {sn} está duplicado en el mismo archivo")
    else:
        seen_serials.add(sn)

    if not pwd:
        errors.append("api_password es obligatorio")
    return len(errors) == 0, errors


@router.post("/import-csv/dry-run", response_model=CsvDryRunResponse)
async def import_csv_dry_run(
    file: UploadFile = File(...),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> CsvDryRunResponse:
    """Paso 1: Validación en seco de archivo CSV para onboarding masivo (máximo 500 filas)."""
    tenant_id = uuid.UUID(claims["tid"])
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo permitido de 2 MB")

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="El archivo debe tener codificación UTF-8 válida")

    reader = csv.DictReader(io.StringIO(decoded))
    serials_res = await db.execute(select(Router.serial_number).where(Router.tenant_id == tenant_id))
    existing_serials = set(serials_res.scalars().all())

    previews = []
    seen_serials: set[str] = set()
    row_num = 1

    for row in reader:
        row_num += 1
        is_valid, errors = _validate_single_csv_row(row, row_num, existing_serials, seen_serials)
        previews.append(
            CsvDryRunRowPreview(
                row_number=row_num,
                display_name=row.get("display_name", f"Fila {row_num}"),
                is_valid=is_valid,
                errors=errors,
            )
        )
        if row_num > 501:
            raise HTTPException(status_code=400, detail="El archivo excede el límite de 500 filas")

    valid_count = sum(1 for p in previews if p.is_valid)
    invalid_count = len(previews) - valid_count
    return CsvDryRunResponse(
        total_rows=len(previews),
        valid_rows_count=valid_count,
        invalid_rows_count=invalid_count,
        can_proceed=invalid_count == 0 and valid_count > 0,
        rows_preview=previews,
    )


@router.post("/import-csv/commit", response_model=CsvCommitResponse)
async def import_csv_commit(
    payload: CsvCommitRequest,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.SUPERVISOR,
            SystemRoleEnum.SUPPORT_L3,
            SystemRoleEnum.INVENTORY_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> CsvCommitResponse:
    """Paso 2: Confirmación e inserción transaccional de routers validados por CSV."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    await _check_tenant_router_quota(db, tenant_id)

    created_ids = []
    for item in payload.rows:
        r = Router(
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
        db.add(r)
        await db.flush()

        for tag_name in item.tags:
            clean_tag = tag_name.strip().lower()
            if clean_tag:
                db.add(RouterTag(tenant_id=tenant_id, router_id=r.id, tag_name=clean_tag))

        aad = f"{tenant_id}:{r.id}".encode("utf-8")
        ct, iv, tag = encrypt_aes_gcm(item.api_password.encode("utf-8"), aad)
        db.add(
            RouterCredentialsVault(
                router_id=r.id,
                tenant_id=tenant_id,
                api_username=item.api_username.strip(),
                current_password_ciphertext=ct,
                current_password_iv=iv,
                current_password_tag=tag,
                auto_rotate_enabled=item.auto_rotate_credentials,
                rotation_interval_days=item.rotation_interval_days,
                updated_by=user_id,
            )
        )
        created_ids.append(r.id)

    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("User-Agent")
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("sub", ""),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=ip_addr,
        actor_user_agent=ua,
        event_category="INVENTORY",
        event_action="ROUTER_IMPORT_CSV_COMMITTED",
        after_state={"imported_count": len(created_ids)},
    )
    await db.commit()
    return CsvCommitResponse(imported_count=len(created_ids), created_router_ids=created_ids)
