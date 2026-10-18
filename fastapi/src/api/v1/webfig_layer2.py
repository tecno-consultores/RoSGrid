# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Motor Dinámico Universal WebFig Capa 2: Catálogo adaptativo, CRUD genérico y comandos CLI."""

import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
)
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.schemas.webfig_layer2 import (
    CatalogMenuGroup,
    CatalogMenuItem,
    ColumnSchemaItem,
    DynamicLayer2CollectionResponse,
    DynamicLayer2CommandRequest,
    DynamicLayer2WriteRequest,
    WebfigLayer2CatalogResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/layer2", tags=["WebFig Layer 2"])

_PATH_REGEX = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9\-*._]+)*$")

_FORBIDDEN_L2_PREFIXES = (
    "user",
    "system/scheduler",
    "ip/service",
)

_GLOBAL_L2_WRITE_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    SystemRoleEnum.TENANT_ADMIN.value,
}


def _validate_l2_path(ros_path: str) -> str:
    cleaned = ros_path.strip().strip("/")
    if not _PATH_REGEX.match(cleaned) or ".." in cleaned or "//" in cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruta REST inválida o sospechosa de Path Traversal: '{ros_path}'",
        )
    for forbidden in _FORBIDDEN_L2_PREFIXES:
        if cleaned == forbidden or cleaned.startswith(f"{forbidden}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso prohibido: La ruta '{cleaned}' está reservada para módulos especializados del sistema.",
            )
    return cleaned


def _check_l2_write_permission(claims: dict[str, Any], perm: UserRouterPermission | None) -> None:
    role = claims.get("rol")
    if role in _GLOBAL_L2_WRITE_ROLES:
        return
    if role == SystemRoleEnum.SUPPORT_L3.value:
        if claims.get("all_r", False) or (perm and perm.can_write_layer2):
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Privilegios insuficientes para mutaciones en WebFig Capa 2 (se requiere can_write_layer2)",
    )


def _infer_type_from_val(val: Any) -> str:
    if isinstance(val, bool) or val in ("true", "false", "yes", "no"):
        return "boolean_ros"
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return "integer"
    return "string"


def _infer_columns(items: list[dict[str, Any]]) -> list[ColumnSchemaItem]:
    if not items:
        return []
    columns: list[ColumnSchemaItem] = []
    seen: set[str] = set()
    for item in items[:10]:
        for k, v in item.items():
            if k in seen:
                continue
            seen.add(k)
            col_type = "readonly_id" if k == ".id" else _infer_type_from_val(v)
            columns.append(
                ColumnSchemaItem(
                    key=k,
                    label=k.replace("-", " ").title(),
                    type=col_type,
                    sortable=k in (".id", "name", "comment", "interface"),
                    editable=k != ".id" and k != "dynamic",
                )
            )
    return columns


def _build_catalog_groups(packages: list[str]) -> list[CatalogMenuGroup]:
    groups = [
        CatalogMenuGroup(
            group="MPLS & VPLS",
            items=[
                CatalogMenuItem(label="MPLS Interfaces", ros_path="mpls/interface", supports_safe_mode=True),
                CatalogMenuItem(label="LDP Instance", ros_path="mpls/ldp", supports_safe_mode=True),
                CatalogMenuItem(label="VPLS Tunnels", ros_path="interface/vpls", supports_safe_mode=True),
            ],
        ),
        CatalogMenuGroup(
            group="Certificates & Security",
            items=[
                CatalogMenuItem(label="Certificates", ros_path="certificate", supports_safe_mode=False),
                CatalogMenuItem(label="IPsec Profiles", ros_path="ip/ipsec/profile", supports_safe_mode=True),
                CatalogMenuItem(label="IPsec Peers", ros_path="ip/ipsec/peer", supports_safe_mode=True),
            ],
        ),
        CatalogMenuGroup(
            group="SNMP & Management",
            items=[
                CatalogMenuItem(label="SNMP Settings", ros_path="snmp", supports_safe_mode=False),
                CatalogMenuItem(label="SNMP Communities", ros_path="snmp/community", supports_safe_mode=False),
                CatalogMenuItem(label="NTP Client", ros_path="system/ntp/client", supports_safe_mode=False),
            ],
        ),
    ]
    pkg_set = set(packages)
    if "container" in pkg_set:
        groups.append(
            CatalogMenuGroup(
                group="Containers",
                items=[
                    CatalogMenuItem(label="OCI Containers", ros_path="container", supports_safe_mode=False),
                    CatalogMenuItem(label="Container Mounts", ros_path="container/mounts", supports_safe_mode=False),
                ],
            )
        )
    if "zerotier" in pkg_set:
        groups.append(
            CatalogMenuGroup(
                group="ZeroTier",
                items=[
                    CatalogMenuItem(label="ZeroTier Instances", ros_path="zerotier", supports_safe_mode=True),
                    CatalogMenuItem(
                        label="ZeroTier Interfaces", ros_path="zerotier/interface", supports_safe_mode=True
                    ),
                ],
            )
        )
    return groups


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/catalog", response_model=WebfigLayer2CatalogResponse)
async def get_catalog(
    router_id: uuid.UUID,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> WebfigLayer2CatalogResponse:
    """Devuelve el árbol jerárquico de menús de Capa 2 adaptado a los paquetes instalados."""
    tenant_id = uuid.UUID(claims["tid"])
    redis = from_deps_redis()
    router_obj, client = await get_router_and_client(router_id, claims, db)

    raw_pkgs = await cached_mikrotik_get(
        redis=redis,
        tenant_id=tenant_id,
        router_id=router_id,
        endpoint="system/package",
        client=client,
        refresh=refresh,
        ttl_seconds=300,
    )
    installed_pkgs = [p.get("name", "") for p in raw_pkgs if isinstance(p, dict)] if isinstance(raw_pkgs, list) else []
    ros_ver = router_obj.ros_version or "7.16"
    tree = _build_catalog_groups(installed_pkgs)

    return WebfigLayer2CatalogResponse(
        router_id=router_id,
        ros_version=ros_ver,
        installed_packages=installed_pkgs,
        menu_tree=tree,
    )


@router.get("/resource/{ros_path:path}", response_model=DynamicLayer2CollectionResponse)
async def get_resource(
    router_id: uuid.UUID,
    ros_path: str,
    refresh: bool = Query(default=False),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> DynamicLayer2CollectionResponse:
    """Lectura universal de colecciones o recursos singleton de Capa 2 con inferencia de esquema."""
    clean_path = _validate_l2_path(ros_path)
    tenant_id = uuid.UUID(claims["tid"])
    redis = from_deps_redis()
    _, client = await get_router_and_client(router_id, claims, db)

    raw_data = await cached_mikrotik_get(
        redis=redis,
        tenant_id=tenant_id,
        router_id=router_id,
        endpoint=clean_path,
        client=client,
        refresh=refresh,
        ttl_seconds=5,
    )
    is_singleton = isinstance(raw_data, dict)
    items = [raw_data] if is_singleton else (raw_data if isinstance(raw_data, list) else [])
    columns = _infer_columns(items)

    return DynamicLayer2CollectionResponse(
        ros_path=clean_path,
        is_singleton=is_singleton,
        supports_safe_mode=True,
        columns_schema=columns,
        items=items,
        form_data=items[0] if is_singleton and items else None,
    )


@router.post("/resource/{ros_path:path}")
async def create_resource(
    router_id: uuid.UUID,
    ros_path: str,
    payload: DynamicLayer2WriteRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Creación universal de registros en Capa 2 protegida por Safe Mode."""
    clean_path = _validate_l2_path(ros_path)
    perm = await _get_user_perm(db, uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"]), router_id)
    _check_l2_write_permission(claims, perm)

    router_obj, client = await get_router_and_client(router_id, claims, db)

    async def _action() -> Any:
        return await client.put(clean_path, payload.attributes)

    if payload.enable_safemode:
        res = await execute_safe_mutation(client, clean_path, "create", _action)
    else:
        res = await _action()

    await write_audit_log(
        session=db,
        tenant_id=uuid.UUID(claims["tid"]),
        actor_username=claims.get("preferred_username", "unknown"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="WEBFIG_L2",
        event_action="L2_RESOURCE_CREATED",
        actor_user_id=uuid.UUID(claims["sub"]),
        router_id=router_id,
        router_display_name=router_obj.display_name,
        ros_rest_method="PUT",
        ros_rest_endpoint=f"/rest/{clean_path}",
        idempotency_key=idempotency_key,
        after_state=payload.attributes,
        status_code=201,
    )
    await db.commit()
    return res


@router.patch("/resource/{ros_path:path}/{item_id}")
async def update_resource(
    router_id: uuid.UUID,
    ros_path: str,
    item_id: str,
    payload: DynamicLayer2WriteRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Edición universal de registro en Capa 2 con antes/después y Safe Mode."""
    clean_path = _validate_l2_path(ros_path)
    perm = await _get_user_perm(db, uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"]), router_id)
    _check_l2_write_permission(claims, perm)

    router_obj, client = await get_router_and_client(router_id, claims, db)
    before_state = await client.get(f"{clean_path}/{item_id}")

    async def _action() -> Any:
        return await client.patch(f"{clean_path}/{item_id}", payload.attributes)

    if payload.enable_safemode:
        res = await execute_safe_mutation(
            client,
            clean_path,
            "update",
            _action,
            item_id=item_id,
            before_state=before_state if isinstance(before_state, dict) else None,
        )
    else:
        res = await _action()

    await write_audit_log(
        session=db,
        tenant_id=uuid.UUID(claims["tid"]),
        actor_username=claims.get("preferred_username", "unknown"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="WEBFIG_L2",
        event_action="L2_RESOURCE_UPDATED",
        actor_user_id=uuid.UUID(claims["sub"]),
        router_id=router_id,
        router_display_name=router_obj.display_name,
        ros_rest_method="PATCH",
        ros_rest_endpoint=f"/rest/{clean_path}/{item_id}",
        idempotency_key=idempotency_key,
        before_state=before_state if isinstance(before_state, dict) else None,
        after_state=payload.attributes,
        status_code=200,
    )
    await db.commit()
    return res


@router.delete("/resource/{ros_path:path}/{item_id}")
async def delete_resource(
    router_id: uuid.UUID,
    ros_path: str,
    item_id: str,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Eliminación universal protegida de registros en Capa 2."""
    clean_path = _validate_l2_path(ros_path)
    perm = await _get_user_perm(db, uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"]), router_id)
    _check_l2_write_permission(claims, perm)

    router_obj, client = await get_router_and_client(router_id, claims, db)
    before_state = await client.get(f"{clean_path}/{item_id}")

    async def _action() -> Any:
        return await client.delete(f"{clean_path}/{item_id}")

    res = await execute_safe_mutation(
        client,
        clean_path,
        "delete",
        _action,
        item_id=item_id,
        before_state=before_state if isinstance(before_state, dict) else None,
    )

    await write_audit_log(
        session=db,
        tenant_id=uuid.UUID(claims["tid"]),
        actor_username=claims.get("preferred_username", "unknown"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="WEBFIG_L2",
        event_action="L2_RESOURCE_DELETED",
        actor_user_id=uuid.UUID(claims["sub"]),
        router_id=router_id,
        router_display_name=router_obj.display_name,
        ros_rest_method="DELETE",
        ros_rest_endpoint=f"/rest/{clean_path}/{item_id}",
        idempotency_key=idempotency_key,
        before_state=before_state if isinstance(before_state, dict) else None,
        status_code=200,
    )
    await db.commit()
    return res


@router.post("/command/{ros_path:path}")
async def execute_command(
    router_id: uuid.UUID,
    ros_path: str,
    payload: DynamicLayer2CommandRequest,
    request: Request,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Ejecución controlada de acciones CLI vía REST (ej. certificate/sign, container/start)."""
    clean_path = _validate_l2_path(ros_path)
    perm = await _get_user_perm(db, uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"]), router_id)
    _check_l2_write_permission(claims, perm)

    router_obj, client = await get_router_and_client(router_id, claims, db)
    res = await client.post(clean_path, payload.arguments)

    await write_audit_log(
        session=db,
        tenant_id=uuid.UUID(claims["tid"]),
        actor_username=claims.get("preferred_username", "unknown"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="WEBFIG_L2",
        event_action="L2_COMMAND_EXECUTED",
        actor_user_id=uuid.UUID(claims["sub"]),
        router_id=router_id,
        router_display_name=router_obj.display_name,
        ros_rest_method="POST",
        ros_rest_endpoint=f"/rest/{clean_path}",
        after_state={"input": payload.arguments, "output": res},
        status_code=200,
    )
    await db.commit()
    return res


def from_deps_redis() -> Any:
    from src.redis_layer.client import get_redis_client

    return get_redis_client()


async def _get_user_perm(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    router_id: uuid.UUID,
) -> UserRouterPermission | None:
    stmt = select(UserRouterPermission).where(
        UserRouterPermission.tenant_id == tenant_id,
        UserRouterPermission.user_id == user_id,
        UserRouterPermission.router_id == router_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()
