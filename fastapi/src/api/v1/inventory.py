# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de Inventario de Equipos MikroTik, Importación Masiva CSV y Re-Pin SSL TOFU."""

import csv
import io
import logging
import uuid
from datetime import UTC, datetime
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
from src.api.v1.inventory_helpers import (
    apply_router_scalar_updates,
    build_router_from_csv,
    build_router_response,
    enrich_router_telemetry,
    perform_discovery,
    row_to_commit_item,
    validate_single_csv_row,
)
from src.core.audit import write_audit_log
from src.core.crypto import decrypt_aes_gcm, encrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum, Tenant, User, UserRouterPermission
from src.models.inventory import (
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterNetworkRoleEnum,
    RouterTag,
    SSLTrustStatusEnum,
    TenantCustomRole,
)
from src.redis_layer.client import get_redis_client
from src.schemas.inventory import (
    CreateRouterRequest,
    CsvCommitRequest,
    CsvCommitResponse,
    CsvCommitRowItem,
    CsvDryRunResponse,
    CsvDryRunRowPreview,
    CustomNetworkRoleCreate,
    CustomNetworkRoleItem,
    NetworkRolesListResponse,
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

DEFAULT_NETWORK_ROLES = [
    "CORE",
    "EDGE_BGP",
    "WAN_BALANCER",
    "BRAS_PPPOE",
    "DISTRIBUTION_SWITCH",
    "TOWER_AP",
    "CORPORATE_CPE",
]


@router.get("/network-roles", response_model=NetworkRolesListResponse)
async def list_network_roles(
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> NetworkRolesListResponse:
    """Lista todos los roles de red disponibles (estándar + personalizados por la empresa)."""
    tenant_id = uuid.UUID(claims["tid"])
    stmt = (
        select(TenantCustomRole)
        .where(TenantCustomRole.tenant_id == tenant_id)
        .order_by(TenantCustomRole.role_name)
    )
    custom_records = (await db.execute(stmt)).scalars().all()

    custom_items = [
        CustomNetworkRoleItem(
            id=r.id,
            role_name=r.role_name,
            description=r.description,
            created_at=r.created_at,
        )
        for r in custom_records
    ]

    all_roles = list(DEFAULT_NETWORK_ROLES)
    for cr in custom_records:
        if cr.role_name not in all_roles:
            all_roles.append(cr.role_name)

    return NetworkRolesListResponse(roles=all_roles, custom_roles=custom_items)


@router.post("/network-roles", response_model=CustomNetworkRoleItem, status_code=status.HTTP_201_CREATED)
async def create_custom_network_role(
    payload: CustomNetworkRoleCreate,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> CustomNetworkRoleItem:
    """Crea un rol de red personalizado para la empresa (exclusivo SuperAdmin y TenantAdmin)."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    role_normalized = payload.role_name.strip().upper()

    if role_normalized in DEFAULT_NETWORK_ROLES:
        raise HTTPException(status_code=400, detail="Este rol ya existe como rol estándar del sistema")

    stmt = select(TenantCustomRole).where(
        TenantCustomRole.tenant_id == tenant_id,
        TenantCustomRole.role_name == role_normalized,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol personalizado con este nombre")

    new_role = TenantCustomRole(
        tenant_id=tenant_id,
        role_name=role_normalized,
        description=payload.description,
        created_at=datetime.now(UTC),
    )
    db.add(new_role)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("preferred_username", claims.get("sub", "")),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="INVENTORY",
        event_action="CUSTOM_NETWORK_ROLE_CREATED",
        after_state={"role_name": role_normalized, "description": payload.description},
    )
    await db.commit()
    await db.refresh(new_role)

    return CustomNetworkRoleItem(
        id=new_role.id,
        role_name=new_role.role_name,
        description=new_role.description,
        created_at=new_role.created_at,
    )


@router.delete("/network-roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_network_role(
    role_name: str,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)
    ),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> None:
    """Elimina un rol de red personalizado de la empresa."""
    tenant_id = uuid.UUID(claims["tid"])
    user_id = uuid.UUID(claims["sub"])
    role_normalized = role_name.strip().upper()

    if role_normalized in DEFAULT_NETWORK_ROLES:
        raise HTTPException(status_code=400, detail="No se pueden eliminar los roles estándar del sistema")

    stmt = select(TenantCustomRole).where(
        TenantCustomRole.tenant_id == tenant_id,
        TenantCustomRole.role_name == role_normalized,
    )
    role_obj = (await db.execute(stmt)).scalar_one_or_none()
    if not role_obj:
        raise HTTPException(status_code=404, detail="Rol personalizado no encontrado")

    await db.delete(role_obj)
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        actor_username=claims.get("preferred_username", claims.get("sub", "")),
        actor_role=claims.get("rol", SystemRoleEnum.TENANT_ADMIN),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="INVENTORY",
        event_action="CUSTOM_NETWORK_ROLE_DELETED",
        before_state={"role_name": role_normalized},
    )
    await db.commit()


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
        telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
        response_items.append(build_router_response(r, telemetry))
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

    aad = f"{tenant_id}:{new_router.id}".encode()
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
            await perform_discovery(client, new_router)

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
    telemetry = await enrich_router_telemetry(redis, tenant_id, new_router.id)
    return build_router_response(new_router, telemetry)


@router.get("/routers/{router_id}", response_model=RouterResponse)
async def get_router(
    router_id: uuid.UUID,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> RouterResponse:
    """Consulta la ficha completa de un equipo MikroTik."""
    tenant_id = uuid.UUID(claims["tid"])
    query = (
        select(Router).options(selectinload(Router.tags)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(r, telemetry)


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
    query = (
        select(Router).options(selectinload(Router.tags)).where(Router.id == router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(query)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Router no encontrado")

    apply_router_scalar_updates(r, payload)

    if payload.tags is not None:
        await db.execute(delete(RouterTag).where(RouterTag.router_id == r.id))
        for tag_name in payload.tags:
            clean_tag = tag_name.strip().lower()
            if clean_tag:
                db.add(RouterTag(tenant_id=tenant_id, router_id=r.id, tag_name=clean_tag))

    await db.commit()
    await db.refresh(r, ["tags"])
    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(r, telemetry)


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
@router.post("/routers/{router_id}/discover", response_model=RouterResponse)
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

    aad = f"{tenant_id}:{r.id}".encode()
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
        await perform_discovery(client, r)

    await db.commit()
    await db.refresh(r, ["tags"])
    redis = get_redis_client()
    telemetry = await enrich_router_telemetry(redis, tenant_id, r.id)
    return build_router_response(r, telemetry)


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
    if (
        not user
        or not user.totp_enabled
        or not user.totp_secret_ciphertext
        or not user.totp_secret_iv
        or not user.totp_secret_tag
    ):
        raise HTTPException(status_code=400, detail="El administrador no tiene 2FA TOTP configurado")

    aad_user = f"{tenant_id}:{user.id}".encode()
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
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="El archivo debe tener codificación UTF-8 válida") from exc

    reader = csv.DictReader(io.StringIO(decoded))
    serials_res = await db.execute(select(Router.serial_number).where(Router.tenant_id == tenant_id))
    existing_serials = set(serials_res.scalars().all())

    previews = []
    seen_serials: set[str] = set()
    row_num = 1

    for row in reader:
        row_num += 1
        is_valid, errors = validate_single_csv_row(row, existing_serials, seen_serials)
        name = (row.get("display_name") or row.get("name") or f"Fila {row_num}").strip()
        url = (row.get("api_base_url") or row.get("ip_address") or row.get("ip") or "").strip()
        sn = (row.get("serial_number") or row.get("serial") or "").strip()
        err_msg = "; ".join(errors) if errors else None
        item = CsvDryRunRowPreview(
            line=row_num,
            row_number=row_num,
            display_name=name,
            ip_address=url,
            serial_number=sn,
            is_valid=is_valid,
            error=err_msg,
            errors=errors,
        )
        previews.append(item)
        if row_num > 501:
            raise HTTPException(status_code=400, detail="El archivo excede el límite de 500 filas")

    valid_count = sum(1 for p in previews if p.is_valid)
    invalid_count = len(previews) - valid_count
    return CsvDryRunResponse(
        total_rows=len(previews),
        valid_rows_count=valid_count,
        invalid_rows_count=invalid_count,
        can_proceed=invalid_count == 0 and valid_count > 0,
        rows=previews,
        rows_preview=previews,
    )


@router.post("/import-csv/commit", response_model=CsvCommitResponse)
async def import_csv_commit(
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

    content_type = request.headers.get("content-type", "")
    items: list[CsvCommitRowItem] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(status_code=400, detail="Debe proporcionar un archivo CSV en el campo 'file'")
        content = await upload.read()
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="El archivo debe tener codificación UTF-8 válida") from exc
        reader = csv.DictReader(io.StringIO(decoded))
        serials_res = await db.execute(select(Router.serial_number).where(Router.tenant_id == tenant_id))
        existing_serials = set(serials_res.scalars().all())
        seen_serials: set[str] = set()
        for row in reader:
            is_valid, _ = validate_single_csv_row(row, existing_serials, seen_serials)
            if is_valid:
                items.append(row_to_commit_item(row))
        if not items:
            raise HTTPException(status_code=400, detail="El archivo CSV no contiene filas válidas para importar")
    else:
        body = await request.json()
        payload = CsvCommitRequest.model_validate(body)
        items = payload.rows

    created_ids = []

    # Auto-registrar roles dinámicos presentes en el CSV que no sean estándar
    standard_roles = {r.value for r in RouterNetworkRoleEnum}
    csv_roles = {
        item.network_role
        for item in items
        if item.network_role and item.network_role not in standard_roles
    }
    if csv_roles:
        existing_custom_res = await db.execute(
            select(TenantCustomRole.role_name).where(
                TenantCustomRole.tenant_id == tenant_id,
                TenantCustomRole.role_name.in_(csv_roles),
            )
        )
        existing_custom_roles = set(existing_custom_res.scalars().all())
        for new_role_name in csv_roles - existing_custom_roles:
            db.add(
                TenantCustomRole(
                    tenant_id=tenant_id,
                    role_name=new_role_name,
                    description="Rol detectado e importado automáticamente desde archivo CSV",
                )
            )

    for item in items:
        r, tags, vault = build_router_from_csv(item, tenant_id, user_id)
        db.add(r)
        db.add(vault)
        for t in tags:
            db.add(t)
        created_ids.append(r.id)

        try:
            host = item.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
            async with MikrotikRestClient(
                host=host,
                port=item.api_port,
                username=item.api_username,
                password=item.api_password,
                timeout=5.0,
            ) as client:
                await perform_discovery(client, r)
        except Exception as exc:
            logger.debug("Discovery en import_csv para %s: %s", r.display_name, exc)

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
