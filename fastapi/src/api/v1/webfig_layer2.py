# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Motor Dinámico Universal WebFig Capa 2: Catálogo, RPC, /console/inspect, .query/.proplist, Bulk y Export .rsc."""

import difflib
import json
import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user_claims
from src.api.v1.webfig_common import (
    cached_mikrotik_get,
    execute_safe_mutation,
    get_router_and_client,
    intercept_maker_checker_if_needed,
    invalidate_webfig_cache,
)
from src.core.audit import write_audit_log
from src.core.crypto import decrypt_aes_gcm
from src.db.session import get_tenant_db_session
from src.models.core import SystemRoleEnum, UserRouterPermission
from src.models.operations import CriticalActionTypeEnum, RouterBackup
from src.schemas.webfig_layer2 import (
    CatalogMenuGroup,
    CatalogMenuItem,
    ColumnSchemaItem,
    DynamicLayer2BulkRequest,
    DynamicLayer2BulkResponse,
    DynamicLayer2CollectionResponse,
    DynamicLayer2CommandRequest,
    DynamicLayer2ExportRequest,
    DynamicLayer2ExportResponse,
    DynamicLayer2QueryRequest,
    DynamicLayer2WriteRequest,
    Layer2InspectResponse,
    Layer2QueryFilterItem,
    Layer2RpcActionDescriptor,
    Layer2RpcParamItem,
    WebfigLayer2CatalogResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routers/{router_id}/webfig/layer2", tags=["WebFig Layer 2"])

_PATH_REGEX = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9\-*._]+)*$")
_PROPLIST_TOKEN_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+$")

_FORBIDDEN_L2_PREFIXES = (
    "user",
    "system/scheduler",
    "ip/service",
)

_GLOBAL_L2_WRITE_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL.value,
    SystemRoleEnum.TENANT_ADMIN.value,
}

# ============================================================================
# CATÁLOGO CANÓNICO DE VERBOS RPC Y ESQUEMAS FALLBACK (/console/inspect)
# ============================================================================

_L2_RPC_ACTIONS_CATALOG: dict[str, list[Layer2RpcActionDescriptor]] = {
    "certificate": [
        Layer2RpcActionDescriptor(
            action="add-acme",
            label="🔐 Emitir Let's Encrypt (ACME)",
            description="Solicita y renueva automáticamente un certificado TLS gratuito vía ACME / Let's Encrypt.",
            ros_endpoint="certificate/enable-ssl-certificate",
            scope="menu",
            requires_safemode=False,
            requires_maker_checker=False,
            parameters_schema=[
                Layer2RpcParamItem(
                    name="dns-name",
                    label="Dominio FQDN (dns-name)",
                    type="string",
                    required=True,
                    default_value="router.isp.local",
                ),
            ],
        ),
        Layer2RpcActionDescriptor(
            action="sign",
            label="✍️ Firmar Certificado",
            description="Firma la plantilla de certificado seleccionada con una Autoridad Certificadora (CA) local.",
            ros_endpoint="certificate/sign",
            scope="row",
            requires_safemode=False,
            requires_maker_checker=True,
            id_param_key="numbers",
            parameters_schema=[
                Layer2RpcParamItem(name="ca", label="CA Firmante (opcional)", type="string", required=False),
                Layer2RpcParamItem(name="name", label="Nombre Final", type="string", required=False),
            ],
        ),
        Layer2RpcActionDescriptor(
            action="export-certificate",
            label="📤 Exportar (.pem / .p12)",
            description="Exporta el certificado y su clave privada en formato PEM o PKCS#12 dentro de /file.",
            ros_endpoint="certificate/export-certificate",
            scope="row",
            requires_safemode=False,
            requires_maker_checker=False,
            id_param_key="numbers",
            parameters_schema=[
                Layer2RpcParamItem(
                    name="type",
                    label="Formato de Exportación",
                    type="enum",
                    required=True,
                    default_value="pem",
                    enum_options=["pem", "pkcs12"],
                ),
                Layer2RpcParamItem(
                    name="export-passphrase",
                    label="Frase de Contraseña (requerida para clave privada)",
                    type="password",
                    required=False,
                ),
                Layer2RpcParamItem(
                    name="file-name",
                    label="Nombre de Archivo Destino",
                    type="string",
                    required=False,
                    default_value="rosgrid-cert-export",
                ),
            ],
        ),
    ],
    "container": [
        Layer2RpcActionDescriptor(
            action="start",
            label="▶️ Iniciar Contenedor",
            description="Inicia la ejecución del contenedor OCI seleccionado.",
            ros_endpoint="container/start",
            scope="row",
            id_param_key="number",
        ),
        Layer2RpcActionDescriptor(
            action="stop",
            label="⏹️ Detener Contenedor",
            description="Detiene de forma ordenada el contenedor OCI seleccionado.",
            ros_endpoint="container/stop",
            scope="row",
            id_param_key="number",
        ),
    ],
    "ip/dhcp-server/lease": [
        Layer2RpcActionDescriptor(
            action="make-static",
            label="📌 Fijar Concesión Estática",
            description="Convierte una concesión DHCP dinámica en reserva estática permanente.",
            ros_endpoint="ip/dhcp-server/lease/make-static",
            scope="row",
            requires_safemode=True,
            id_param_key="numbers",
        ),
    ],
    "ip/arp": [
        Layer2RpcActionDescriptor(
            action="make-static",
            label="📌 Fijar ARP Estático",
            description="Convierte una entrada ARP aprendida dinámicamente en estática.",
            ros_endpoint="ip/arp/make-static",
            scope="row",
            requires_safemode=True,
            id_param_key="numbers",
        ),
    ],
    "system/script": [
        Layer2RpcActionDescriptor(
            action="run",
            label="⚡ Ejecutar Script",
            description="Ejecuta el script almacenado en RouterOS v7 con trazabilidad WORM.",
            ros_endpoint="system/script/run",
            scope="row",
            requires_safemode=True,
            requires_maker_checker=True,
            id_param_key="number",
        ),
    ],
}

_FALLBACK_INSPECT_SCHEMAS: dict[str, list[ColumnSchemaItem]] = {
    "certificate": [
        ColumnSchemaItem(key=".id", label="ID", type="readonly_id", sortable=True, editable=False),
        ColumnSchemaItem(
            key="name",
            label="Name",
            type="string",
            sortable=True,
            required=True,
            description="Nombre identificador único del certificado en RouterOS.",
        ),
        ColumnSchemaItem(
            key="common-name",
            label="Common Name",
            type="string",
            sortable=True,
            required=True,
            description="CN (FQDN o identidad) del sujeto X.509.",
        ),
        ColumnSchemaItem(
            key="key-type",
            label="Key Type",
            type="enum",
            default_value="rsa",
            enum_options=["rsa", "ec"],
            description="Algoritmo criptográfico de llave pública.",
        ),
        ColumnSchemaItem(
            key="key-size",
            label="Key Size",
            type="enum",
            default_value="2048",
            enum_options=["2048", "4096", "prime256v1", "secp384r1"],
            description="Longitud de bits RSA o curva elíptica.",
        ),
        ColumnSchemaItem(
            key="days-valid",
            label="Days Valid",
            type="integer",
            default_value="825",
            description="Período de validez del certificado en días.",
        ),
        ColumnSchemaItem(
            key="trusted",
            label="Trusted",
            type="boolean_ros",
            default_value="true",
            description="Confiar en este certificado dentro de la cadena TLS del router.",
        ),
        ColumnSchemaItem(key="comment", label="Comment", type="string", sortable=True),
    ],
    "mpls/interface": [
        ColumnSchemaItem(key=".id", label="ID", type="readonly_id", sortable=True, editable=False),
        ColumnSchemaItem(
            key="interface",
            label="Interface",
            type="string",
            sortable=True,
            required=True,
            default_value="all",
            description="Interfaz física o 'all' para etiquetado MPLS.",
        ),
        ColumnSchemaItem(
            key="mpls-mtu",
            label="Mpls Mtu",
            type="integer",
            default_value="1508",
            description="MTU máximo de tramas MPLS (1508 o 1526 para VPLS).",
        ),
        ColumnSchemaItem(key="disabled", label="Disabled", type="boolean_ros", default_value="false"),
        ColumnSchemaItem(key="comment", label="Comment", type="string", sortable=True),
    ],
    "snmp/community": [
        ColumnSchemaItem(key=".id", label="ID", type="readonly_id", sortable=True, editable=False),
        ColumnSchemaItem(key="name", label="Name", type="string", sortable=True, required=True),
        ColumnSchemaItem(key="addresses", label="Addresses", type="string", default_value="0.0.0.0/0"),
        ColumnSchemaItem(
            key="security",
            label="Security",
            type="enum",
            default_value="private",
            enum_options=["none", "authorized", "private"],
        ),
        ColumnSchemaItem(
            key="authentication-protocol",
            label="Auth Protocol",
            type="enum",
            default_value="SHA256",
            enum_options=["MD5", "SHA1", "SHA256", "SHA512"],
        ),
        ColumnSchemaItem(
            key="encryption-protocol",
            label="Encryption Protocol",
            type="enum",
            default_value="AES",
            enum_options=["DES", "AES"],
        ),
        ColumnSchemaItem(key="read-access", label="Read Access", type="boolean_ros", default_value="true"),
        ColumnSchemaItem(key="write-access", label="Write Access", type="boolean_ros", default_value="false"),
    ],
}

_DEFAULT_EMPTY_SCHEMA: list[ColumnSchemaItem] = [
    ColumnSchemaItem(key=".id", label="ID", type="readonly_id", sortable=True, editable=False),
    ColumnSchemaItem(key="name", label="Name", type="string", sortable=True, required=True),
    ColumnSchemaItem(key="disabled", label="Disabled", type="boolean_ros", default_value="false"),
    ColumnSchemaItem(key="comment", label="Comment", type="string", sortable=True),
]


# ============================================================================
# VALIDADORES Y UTILIDADES PURAS (CC <= 5)
# ============================================================================


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
    if role == SystemRoleEnum.SUPPORT_L3.value and (claims.get("all_r", False) or (perm and perm.can_write_layer2)):
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


def _build_column_schema_item(key: str, sample_val: Any) -> ColumnSchemaItem:
    col_type = "readonly_id" if key == ".id" else _infer_type_from_val(sample_val)
    return ColumnSchemaItem(
        key=key,
        label=key.replace("-", " ").title(),
        type=col_type,
        sortable=key in (".id", "name", "comment", "interface", "common-name"),
        editable=key not in (".id", "dynamic", "expired", "revoked", "invalid"),
    )


def _infer_columns(items: list[dict[str, Any]]) -> list[ColumnSchemaItem]:
    if not items:
        return []
    columns: list[ColumnSchemaItem] = []
    seen: set[str] = set()
    for item in items[:10]:
        for k, v in item.items():
            if k not in seen:
                seen.add(k)
                columns.append(_build_column_schema_item(k, v))
    return columns


def get_rpc_actions_for_path(clean_path: str) -> list[Layer2RpcActionDescriptor]:
    """Devuelve la lista de acciones RPC permitidas para un submenú de Capa 2."""
    return list(_L2_RPC_ACTIONS_CATALOG.get(clean_path, []))


def _parse_inspect_entry(entry: dict[str, Any]) -> ColumnSchemaItem | None:
    symbol = str(entry.get("symbol") or entry.get("name") or "").strip()
    if not symbol or symbol.startswith("<") or symbol in ("from", "copy-from", "place-before", "numbers"):
        return None
    desc_text = str(entry.get("text") or "").strip() or None
    col_type = "boolean_ros" if symbol in ("disabled", "trusted", "enabled") else "string"
    return ColumnSchemaItem(
        key=symbol,
        label=symbol.replace("-", " ").title(),
        type=col_type,
        sortable=symbol in ("name", "comment", "interface", "common-name"),
        editable=True,
        description=desc_text[:400] if desc_text else None,
    )


def _parse_console_inspect_syntax(clean_path: str, raw_inspect: Any) -> list[ColumnSchemaItem]:
    """Transforma la salida de /rest/console/inspect en ColumnSchemaItem[] o aplica fallback tipado."""
    if not isinstance(raw_inspect, list) or not raw_inspect:
        return list(_FALLBACK_INSPECT_SCHEMAS.get(clean_path, _DEFAULT_EMPTY_SCHEMA))
    cols: list[ColumnSchemaItem] = [
        ColumnSchemaItem(key=".id", label="ID", type="readonly_id", sortable=True, editable=False)
    ]
    seen = {".id"}
    for item in raw_inspect:
        if isinstance(item, dict):
            parsed = _parse_inspect_entry(item)
            if parsed and parsed.key not in seen:
                seen.add(parsed.key)
                cols.append(parsed)
    if len(cols) <= 1:
        return list(_FALLBACK_INSPECT_SCHEMAS.get(clean_path, _DEFAULT_EMPTY_SCHEMA))
    return cols


async def _get_cached_l2_schema(redis: Any, cache_key: str) -> list[ColumnSchemaItem] | None:
    if not redis:
        return None
    try:
        cached = await redis.get(cache_key)
        if cached:
            raw_list = json.loads(cached)
            return [ColumnSchemaItem(**c) for c in raw_list]
    except Exception as exc:
        logger.debug("Error leyendo caché l2_schema: %s", exc)
    return None


async def _set_cached_l2_schema(redis: Any, cache_key: str, cols: list[ColumnSchemaItem]) -> None:
    if not redis or not cols:
        return
    try:
        await redis.setex(cache_key, 86400, json.dumps([c.model_dump() for c in cols]))
    except Exception as exc:
        logger.debug("Error guardando caché l2_schema: %s", exc)


async def _resolve_schema_via_inspect(
    redis: Any,
    tenant_id: uuid.UUID,
    ros_version: str,
    clean_path: str,
    client: Any,
) -> tuple[list[ColumnSchemaItem], str]:
    """Consulta KeyDB o /rest/console/inspect para obtener el esquema de un submenú vacío."""
    cache_key = f"rg:{tenant_id}:l2_schema:{ros_version}:{clean_path}"
    cached_cols = await _get_cached_l2_schema(redis, cache_key)
    if cached_cols is not None:
        return cached_cols, "console_inspect"

    inspect_path = f"{clean_path.replace('/', ',')},add"
    raw_inspect: Any = None
    try:
        raw_inspect = await client.post("console/inspect", {"request": "syntax", "path": inspect_path})
    except Exception as exc:
        logger.debug("Fallback de /console/inspect para %s: %s", clean_path, exc)

    cols = _parse_console_inspect_syntax(clean_path, raw_inspect)
    source = "console_inspect" if isinstance(raw_inspect, list) and len(raw_inspect) > 0 else "fallback"
    await _set_cached_l2_schema(redis, cache_key, cols)
    return cols, source


def _normalize_proplist(proplist_raw: str | list[str] | None) -> list[str]:
    """Valida y normaliza una lista de propiedades .proplist asegurando siempre '.id'."""
    if not proplist_raw or not isinstance(proplist_raw, (str, list)):
        return []
    tokens = proplist_raw.split(",") if isinstance(proplist_raw, str) else list(proplist_raw)
    cleaned: list[str] = [".id"]
    for tok in tokens:
        t = tok.strip()
        if not t or t == ".id":
            continue
        if not _PROPLIST_TOKEN_REGEX.match(t):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Atributo inválido en .proplist: '{t}'",
            )
        if t not in cleaned:
            cleaned.append(t)
    return cleaned


def _build_ros_query_stack(filters: list[Layer2QueryFilterItem]) -> list[str]:
    """Construye la pila RPN .query compatible con POST /rest/<menu>/print de RouterOS v7."""
    if not filters:
        return []
    query_tokens: list[str] = []
    for f in filters:
        if f.operator == "!=":
            query_tokens.append(f"{f.field}={f.value}")
            query_tokens.append("#!")
        else:
            query_tokens.append(f"{f.field}{f.operator}{f.value}")
    if len(filters) > 1:
        for _ in range(len(filters) - 1):
            query_tokens.append("#&")
    return query_tokens


def _filter_items_locally(
    items: list[dict[str, Any]],
    filters: list[Layer2QueryFilterItem],
    proplist: list[str],
) -> list[dict[str, Any]]:
    """Aplica filtrado y proyección determinista sobre los registros devueltos."""
    result: list[dict[str, Any]] = []
    for row in items:
        if not _row_matches_all_filters(row, filters):
            continue
        if proplist:
            result.append({k: row[k] for k in proplist if k in row})
        else:
            result.append(row)
    return result


def _row_matches_all_filters(row: dict[str, Any], filters: list[Layer2QueryFilterItem]) -> bool:
    for f in filters:
        actual = str(row.get(f.field, ""))
        if f.operator == "=" and actual != f.value:
            return False
        if f.operator == "!=" and actual == f.value:
            return False
    return True


def _extract_rsc_section_for_path(full_rsc: str, clean_path: str) -> str:
    """Extrae únicamente el bloque CLI correspondiente a /<submenu> de un archivo .rsc completo."""
    if not full_rsc.strip():
        return ""
    cli_header = f"/{clean_path.replace('/', ' ')}"
    extracted: list[str] = []
    in_section = False
    for line in full_rsc.splitlines():
        stripped = line.strip()
        if stripped.startswith("/"):
            in_section = stripped == cli_header or stripped.startswith(f"{cli_header} ")
        if in_section:
            extracted.append(line)
    return "\n".join(extracted).strip()


def _synthesize_rsc_from_items(clean_path: str, items: list[dict[str, Any]]) -> str:
    """Genera representación CLI .rsc determinista cuando el router devuelve lista de objetos."""
    cli_header = f"/{clean_path.replace('/', ' ')}"
    lines = [cli_header]
    for item in items:
        if not isinstance(item, dict):
            continue
        pairs = [
            f"{k}={v}"
            for k, v in sorted(item.items())
            if k not in (".id", "id", "dynamic") and v not in (None, "")
        ]
        if pairs:
            lines.append("add " + " ".join(pairs))
    return "\n".join(lines) + "\n"


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


@router.get("/rpc-catalog/{ros_path:path}", response_model=list[Layer2RpcActionDescriptor])
async def get_rpc_catalog(
    router_id: uuid.UUID,
    ros_path: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> list[Layer2RpcActionDescriptor]:
    """Devuelve el catálogo de verbos RPC contextuales soportados por un submenú de Capa 2."""
    clean_path = _validate_l2_path(ros_path)
    await get_router_and_client(router_id, claims, db)
    return get_rpc_actions_for_path(clean_path)


@router.get("/inspect/{ros_path:path}", response_model=Layer2InspectResponse)
async def inspect_layer2_schema(
    router_id: uuid.UUID,
    ros_path: str,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Layer2InspectResponse:
    """Introspección automática de esquema y autocompletado mediante /rest/console/inspect."""
    clean_path = _validate_l2_path(ros_path)
    tenant_id = uuid.UUID(claims["tid"])
    redis = from_deps_redis()
    router_obj, client = await get_router_and_client(router_id, claims, db)
    ros_ver = router_obj.ros_version or "7.16"

    cols, source = await _resolve_schema_via_inspect(redis, tenant_id, ros_ver, clean_path, client)
    rpc_actions = get_rpc_actions_for_path(clean_path)
    return Layer2InspectResponse(
        ros_path=clean_path,
        ros_version=ros_ver,
        schema_source=source,
        columns_schema=cols,
        available_rpc_actions=rpc_actions,
        completions=[c.key for c in cols if c.editable],
    )


@router.get("/resource/{ros_path:path}", response_model=DynamicLayer2CollectionResponse)
async def get_resource(
    router_id: uuid.UUID,
    ros_path: str,
    refresh: bool = Query(default=False),
    proplist: str | None = Query(default=None, max_length=600),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> DynamicLayer2CollectionResponse:
    """Lectura universal de colecciones o recursos singleton de Capa 2 con fallback /console/inspect."""
    clean_path = _validate_l2_path(ros_path)
    normalized_props = _normalize_proplist(proplist)
    tenant_id = uuid.UUID(claims["tid"])
    redis = from_deps_redis()
    router_obj, client = await get_router_and_client(router_id, claims, db)

    endpoint_query = f"{clean_path}?.proplist={','.join(normalized_props)}" if normalized_props else clean_path
    raw_data = await cached_mikrotik_get(
        redis=redis,
        tenant_id=tenant_id,
        router_id=router_id,
        endpoint=endpoint_query,
        client=client,
        refresh=refresh,
        ttl_seconds=5,
    )
    is_singleton = isinstance(raw_data, dict)
    items = [raw_data] if is_singleton else (raw_data if isinstance(raw_data, list) else [])
    columns = _infer_columns(items)
    schema_source = "inferred"

    if not columns:
        ros_ver = router_obj.ros_version or "7.16"
        columns, schema_source = await _resolve_schema_via_inspect(redis, tenant_id, ros_ver, clean_path, client)

    return DynamicLayer2CollectionResponse(
        ros_path=clean_path,
        is_singleton=is_singleton,
        supports_safe_mode=True,
        columns_schema=columns,
        items=items,
        form_data=items[0] if is_singleton and items else None,
        available_rpc_actions=get_rpc_actions_for_path(clean_path),
        schema_source=schema_source,
        is_server_filtered=bool(normalized_props),
    )


@router.post("/query/{ros_path:path}", response_model=DynamicLayer2CollectionResponse)
async def query_resource_server_side(
    router_id: uuid.UUID,
    ros_path: str,
    payload: DynamicLayer2QueryRequest,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> DynamicLayer2CollectionResponse:
    """Filtrado Server-Side (.query) y proyección de columnas (.proplist) en el motor C++ de RouterOS v7."""
    clean_path = _validate_l2_path(ros_path)
    normalized_props = _normalize_proplist(payload.proplist)
    query_stack = _build_ros_query_stack(payload.filters)
    tenant_id = uuid.UUID(claims["tid"])
    redis = from_deps_redis()
    router_obj, client = await get_router_and_client(router_id, claims, db)

    print_body: dict[str, Any] = {}
    if normalized_props:
        print_body[".proplist"] = normalized_props
    if query_stack:
        print_body[".query"] = query_stack

    try:
        raw_res = await client.post(f"{clean_path}/print", print_body)
        items = raw_res if isinstance(raw_res, list) else []
    except Exception:
        fallback_data = await cached_mikrotik_get(
            redis=redis,
            tenant_id=tenant_id,
            router_id=router_id,
            endpoint=clean_path,
            client=client,
            refresh=False,
            ttl_seconds=5,
        )
        raw_items = fallback_data if isinstance(fallback_data, list) else []
        items = _filter_items_locally(raw_items, payload.filters, normalized_props)

    columns = _infer_columns(items)
    schema_source = "inferred"
    if not columns:
        ros_ver = router_obj.ros_version or "7.16"
        columns, schema_source = await _resolve_schema_via_inspect(redis, tenant_id, ros_ver, clean_path, client)

    reduction_pct = round(max(0.0, (1.0 - (len(normalized_props) / 35.0)) * 100.0), 1) if normalized_props else 0.0
    return DynamicLayer2CollectionResponse(
        ros_path=clean_path,
        is_singleton=False,
        supports_safe_mode=True,
        columns_schema=columns,
        items=items,
        available_rpc_actions=get_rpc_actions_for_path(clean_path),
        schema_source=schema_source,
        is_server_filtered=True,
        payload_reduction_pct=reduction_pct,
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

    res = await execute_safe_mutation(client, clean_path, "create", _action) if payload.enable_safemode else await _action()
    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)

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
    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)

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
    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)

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


async def _apply_single_bulk_op(
    client: Any,
    clean_path: str,
    action: str,
    item_id: str,
    comment: str | None,
) -> dict[str, Any]:
    """Ejecuta una operación individual dentro de un lote de Capa 2."""
    if action == "remove":
        await client.delete(f"{clean_path}/{item_id}")
        return {"item_id": item_id, "status": "DELETED"}
    patch_body: dict[str, Any] = {}
    if action == "enable":
        patch_body["disabled"] = "false"
    elif action == "disable":
        patch_body["disabled"] = "true"
    elif action == "comment":
        patch_body["comment"] = comment or ""
    await client.patch(f"{clean_path}/{item_id}", patch_body)
    return {"item_id": item_id, "status": "UPDATED", "applied": patch_body}


@router.post("/bulk/{ros_path:path}", response_model=DynamicLayer2BulkResponse)
async def execute_bulk_operation(
    router_id: uuid.UUID,
    ros_path: str,
    payload: DynamicLayer2BulkRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> DynamicLayer2BulkResponse:
    """Operaciones por lote (enable, disable, comment, remove) bajo ventana única de Safe Mode (60s)."""
    clean_path = _validate_l2_path(ros_path)
    perm = await _get_user_perm(db, uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"]), router_id)
    _check_l2_write_permission(claims, perm)
    router_obj, client = await get_router_and_client(router_id, claims, db)

    results: list[dict[str, Any]] = []

    async def _batch_action() -> list[dict[str, Any]]:
        for item_id in payload.item_ids:
            res_item = await _apply_single_bulk_op(client, clean_path, payload.action, item_id, payload.comment)
            results.append(res_item)
        return results

    if payload.enable_safemode:
        await execute_safe_mutation(client, clean_path, f"bulk_{payload.action}", _batch_action)
    else:
        await _batch_action()

    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)
    await write_audit_log(
        session=db,
        tenant_id=uuid.UUID(claims["tid"]),
        actor_username=claims.get("preferred_username", "unknown"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="WEBFIG_L2",
        event_action="L2_BULK_MUTATION_EXECUTED",
        actor_user_id=uuid.UUID(claims["sub"]),
        router_id=router_id,
        router_display_name=router_obj.display_name,
        ros_rest_method="PATCH" if payload.action != "remove" else "DELETE",
        ros_rest_endpoint=f"/rest/{clean_path}",
        idempotency_key=idempotency_key,
        after_state={"action": payload.action, "item_ids": payload.item_ids, "comment": payload.comment},
        status_code=200,
    )
    await db.commit()
    return DynamicLayer2BulkResponse(
        ros_path=clean_path,
        action=payload.action,
        total_requested=len(payload.item_ids),
        succeeded_count=len(results),
        failed_count=0,
        safemode_applied=payload.enable_safemode,
        results=results,
    )


async def _fetch_live_submenu_rsc(client: Any, clean_path: str, mode: str) -> str:
    """Obtiene el bloque .rsc en vivo del submenú mediante /export o síntesis determinista."""
    try:
        export_args = {"terse": "true"} if mode == "terse" else {"compact": "true"}
        raw_export = await client.post(f"{clean_path}/export", export_args)
        if isinstance(raw_export, str) and raw_export.strip():
            return raw_export.strip() + "\n"
        if isinstance(raw_export, dict) and str(raw_export.get("ret", "")).strip():
            return str(raw_export["ret"]).strip() + "\n"
    except Exception as exc:
        logger.debug("Fallback a síntesis .rsc desde GET /rest/%s: %s", clean_path, exc)

    raw_items = await client.get(clean_path)
    items = [raw_items] if isinstance(raw_items, dict) else (raw_items if isinstance(raw_items, list) else [])
    return _synthesize_rsc_from_items(clean_path, items)


async def _fetch_latest_backup_section(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    clean_path: str,
) -> tuple[str, str | None]:
    """Busca el último respaldo en router_backups y extrae la sección CLI correspondiente."""
    stmt = (
        select(RouterBackup)
        .where(RouterBackup.tenant_id == tenant_id, RouterBackup.router_id == router_id)
        .order_by(desc(RouterBackup.created_at))
        .limit(1)
    )
    res = await db.execute(stmt)
    latest_bk = res.scalar_one_or_none() if res is not None and hasattr(res, "scalar_one_or_none") else None
    if not isinstance(latest_bk, RouterBackup):
        return f"/{clean_path.replace('/', ' ')}\n", None

    try:
        aad = f"{tenant_id}:{router_id}".encode()
        full_rsc = decrypt_aes_gcm(latest_bk.rsc_ciphertext, latest_bk.rsc_iv, latest_bk.rsc_tag, aad).decode("utf-8")
        section = _extract_rsc_section_for_path(full_rsc, clean_path)
        ts_str = latest_bk.created_at.isoformat() if latest_bk.created_at else None
        return (section + "\n" if section else f"/{clean_path.replace('/', ' ')}\n"), ts_str
    except Exception as exc:
        logger.debug("No se pudo desencriptar último backup para diff L2: %s", exc)
        return f"/{clean_path.replace('/', ' ')}\n", None


@router.post("/export/{ros_path:path}", response_model=DynamicLayer2ExportResponse)
async def export_layer2_submenu(
    router_id: uuid.UUID,
    ros_path: str,
    payload: DynamicLayer2ExportRequest,
    request: Request,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> DynamicLayer2ExportResponse:
    """Exportación contextual .rsc de un submenú de Capa 2 y comparación Diff contra el último respaldo Git."""
    clean_path = _validate_l2_path(ros_path)
    tenant_id = uuid.UUID(claims["tid"])
    router_obj, client = await get_router_and_client(router_id, claims, db)

    live_rsc = await _fetch_live_submenu_rsc(client, clean_path, payload.mode)
    backup_rsc, latest_ts = (
        await _fetch_latest_backup_section(db, tenant_id, router_id, clean_path)
        if payload.compare_with_latest_backup
        else ("", None)
    )

    cli_header = f"/{clean_path.replace('/', ' ')}"
    diff_lines = list(
        difflib.unified_diff(
            backup_rsc.splitlines(),
            live_rsc.splitlines(),
            fromfile=f"backup:{cli_header}",
            tofile=f"live:{cli_header}",
            lineterm="",
        )
    )
    unified_diff = "\n".join(diff_lines)
    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_username=claims.get("preferred_username", "unknown"),
        actor_role=claims.get("rol", SystemRoleEnum.SUPPORT_L3.value),
        actor_ip=request.client.host if request.client else "127.0.0.1",
        event_category="WEBFIG_L2",
        event_action="L2_SUBMENU_EXPORTED",
        actor_user_id=uuid.UUID(claims["sub"]),
        router_id=router_id,
        router_display_name=router_obj.display_name,
        ros_rest_method="POST",
        ros_rest_endpoint=f"/rest/{clean_path}/export",
        after_state={"mode": payload.mode, "has_drift": bool(unified_diff)},
        status_code=200,
    )
    await db.commit()
    return DynamicLayer2ExportResponse(
        ros_path=clean_path,
        cli_header=cli_header,
        live_rsc_text=live_rsc,
        backup_rsc_text=backup_rsc,
        unified_diff=unified_diff,
        has_drift=bool(unified_diff),
        latest_backup_timestamp=latest_ts,
    )


def _resolve_rpc_target_and_args(
    clean_path: str,
    payload: DynamicLayer2CommandRequest,
) -> tuple[str, dict[str, Any], Layer2RpcActionDescriptor | None]:
    """Resuelve el endpoint REST final, inyecta el ID de fila si aplica y retorna el descriptor RPC."""
    args = dict(payload.arguments)
    if not payload.action:
        return clean_path, args, None

    target_ep = f"{clean_path}/{payload.action.strip('/')}"
    catalog = get_rpc_actions_for_path(clean_path)
    descriptor = next((d for d in catalog if d.action == payload.action), None)
    if payload.item_id:
        id_key = descriptor.id_param_key if descriptor else "numbers"
        args.setdefault(id_key, payload.item_id)
    return target_ep, args, descriptor


@router.post("/command/{ros_path:path}")
async def execute_command(
    router_id: uuid.UUID,
    ros_path: str,
    payload: DynamicLayer2CommandRequest,
    request: Request,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_tenant_db_session),
) -> Any:
    """Ejecución controlada de acciones RPC vía REST (ej. certificate/sign, certificate/add-acme, container/start)."""
    clean_path = _validate_l2_path(ros_path)
    target_ep, rpc_args, descriptor = _resolve_rpc_target_and_args(clean_path, payload)

    if descriptor and descriptor.requires_maker_checker:
        intercepted = await intercept_maker_checker_if_needed(
            db=db,
            claims=claims,
            router_id=router_id,
            summary=f"Acción RPC Capa 2: /{target_ep}",
            ros_rest_method="POST",
            ros_rest_path=target_ep,
            request_payload=rpc_args,
            action_type=CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT,
        )
        if intercepted is not None:
            return intercepted

    perm = await _get_user_perm(db, uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"]), router_id)
    _check_l2_write_permission(claims, perm)

    router_obj, client = await get_router_and_client(router_id, claims, db)
    use_sm = payload.enable_safemode or (descriptor.requires_safemode if descriptor else False)

    async def _rpc_call() -> Any:
        return await client.post(target_ep, rpc_args)

    res = await execute_safe_mutation(client, clean_path, "rpc", _rpc_call) if use_sm else await _rpc_call()
    await invalidate_webfig_cache(from_deps_redis(), uuid.UUID(claims["tid"]), router_id, clean_path)

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
        ros_rest_endpoint=f"/rest/{target_ep}",
        after_state={"input": rpc_args, "output": res},
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
