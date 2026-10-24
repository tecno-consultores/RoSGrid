# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Endpoints de IPAM Dual-Stack Universal y Gestión de Servicios de Abonados."""

import ipaddress
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user_claims, require_roles
from src.api.v1.webfig_common import _create_client_from_vault
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.models.ipam import (
    CustomerService,
    CustomerServiceStatusEnum,
    IPAddressStatusEnum,
    IPAMAddress,
    IPAMPrefix,
    IPAMVrf,
    IPFamilyEnum,
    IPPrefixRoleEnum,
    IPPrefixStatusEnum,
)
from src.schemas.ipam import (
    CustomerServiceCreate,
    CustomerServiceResponse,
    IPAMAddressCreate,
    IPAMAddressResponse,
    IPAMPrefixCreate,
    IPAMPrefixNextAvailableResponse,
    IPAMPrefixResponse,
    IPAMVrfCreate,
    IPAMVrfResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ipam", tags=["IPAM & Customer Services"])


def get_tenant_id(claims: dict[str, Any]) -> uuid.UUID:
    tid = claims.get("tid") or claims.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant ID no encontrado en sesión")
    return uuid.UUID(str(tid))


# ============================================================================
# 1. VRFs
# ============================================================================
@router.get("/vrfs", response_model=list[IPAMVrfResponse])
async def list_vrfs(
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista todas las VRFs configuradas en el tenant."""
    tenant_id = get_tenant_id(claims)
    stmt = select(IPAMVrf).where(IPAMVrf.tenant_id == tenant_id).order_by(IPAMVrf.name.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/vrfs", response_model=IPAMVrfResponse, status_code=status.HTTP_201_CREATED)
async def create_vrf(
    payload: IPAMVrfCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)
    ),
) -> Any:
    """Crea una nueva VRF en el IPAM."""
    tenant_id = get_tenant_id(claims)
    # Verificar nombre duplicado
    stmt_check = select(IPAMVrf).where(IPAMVrf.tenant_id == tenant_id, IPAMVrf.name == payload.name)
    existing = (await db.execute(stmt_check)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"La VRF '{payload.name}' ya existe")

    vrf = IPAMVrf(
        tenant_id=tenant_id,
        name=payload.name,
        route_distinguisher=payload.route_distinguisher,
        description=payload.description,
    )
    db.add(vrf)
    await db.commit()
    await db.refresh(vrf)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="IPAM_VRF_CREATED",
        status_code=201,
        after_state={"vrf_id": str(vrf.id), "name": vrf.name},
    )
    return vrf


# ============================================================================
# 2. PREFIJOS Y SUPERNETS (Árbol CIDR)
# ============================================================================
@router.get("/prefixes", response_model=list[IPAMPrefixResponse])
async def list_prefixes(
    vrf_id: Optional[uuid.UUID] = Query(None),
    ip_family: Optional[IPFamilyEnum] = Query(None),
    role: Optional[IPPrefixRoleEnum] = Query(None),
    auto_sync: bool = Query(True),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista prefijos y subredes con filtros por VRF, Familia de IP y Rol."""
    tenant_id = get_tenant_id(claims)

    # Si el tenant no tiene ningún prefijo registrado, auto-descubrir desde la flota alcanzable
    if auto_sync and not vrf_id and not ip_family and not role:
        existing_pfxs = (
            await db.execute(select(IPAMPrefix.id).where(IPAMPrefix.tenant_id == tenant_id))
        ).scalars().all()
        if not existing_pfxs:
            logger.info(f"Tenant {tenant_id} sin prefijos en IPAM. Iniciando auto-descubrimiento desde la flota...")
            try:
                await _sync_all_tenant_routers_ipam(tenant_id, db)
            except Exception as e:
                logger.warning(f"Error en auto-descubrimiento IPAM inicial: {e}")

    stmt = select(IPAMPrefix).where(IPAMPrefix.tenant_id == tenant_id)
    if vrf_id:
        stmt = stmt.where(IPAMPrefix.vrf_id == vrf_id)
    if ip_family:
        stmt = stmt.where(IPAMPrefix.ip_family == ip_family)
    if role:
        stmt = stmt.where(IPAMPrefix.role == role)

    stmt = stmt.order_by(IPAMPrefix.prefix.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/prefixes", response_model=IPAMPrefixResponse, status_code=status.HTTP_201_CREATED)
async def create_prefix(
    payload: IPAMPrefixCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)
    ),
) -> Any:
    """Registra un nuevo prefijo o subred CIDR validada matemáticamente."""
    tenant_id = get_tenant_id(claims)

    # Validar notación CIDR estricta
    try:
        network_obj = ipaddress.ip_network(payload.prefix, strict=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Formato CIDR inválido: {e}"
        ) from e

    # Verificar concordancia con ip_family
    if (payload.ip_family == IPFamilyEnum.IPv4 and network_obj.version != 4) or (
        payload.ip_family == IPFamilyEnum.IPv6 and network_obj.version != 6
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El prefijo '{payload.prefix}' no concuerda con la familia {payload.ip_family}",
        )

    # Verificar solapamientos o duplicados en la misma VRF
    stmt_dup = select(IPAMPrefix).where(
        IPAMPrefix.tenant_id == tenant_id,
        IPAMPrefix.vrf_id == payload.vrf_id,
        IPAMPrefix.prefix == str(network_obj),
    )
    if (await db.execute(stmt_dup)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"El prefijo {network_obj} ya está registrado en esta VRF"
        )

    prefix = IPAMPrefix(
        tenant_id=tenant_id,
        vrf_id=payload.vrf_id,
        parent_id=payload.parent_id,
        prefix=str(network_obj),
        ip_family=payload.ip_family,
        role=payload.role,
        status=payload.status,
        is_pool=payload.is_pool,
        default_child_prefix_len=payload.default_child_prefix_len,
        description=payload.description,
        utilization_pct=Decimal("0.00"),
    )
    db.add(prefix)
    await db.commit()
    await db.refresh(prefix)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="IPAM_PREFIX_CREATED",
        status_code=201,
        after_state={"prefix_id": str(prefix.id), "prefix": prefix.prefix, "role": prefix.role},
    )
    return prefix


@router.get("/prefixes/{prefix_id}/next-available", response_model=IPAMPrefixNextAvailableResponse)
async def get_next_available_resource(
    prefix_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Calcula la siguiente IP libre o el siguiente prefijo delegado (/56) dentro del bloque."""
    tenant_id = get_tenant_id(claims)
    stmt_p = select(IPAMPrefix).where(IPAMPrefix.id == prefix_id, IPAMPrefix.tenant_id == tenant_id)
    prefix = (await db.execute(stmt_p)).scalar_one_or_none()
    if not prefix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefijo no encontrado")

    net = ipaddress.ip_network(prefix.prefix)

    # Caso A: IPv6 con delegación de subredes (ej: /56 desde un /48)
    if net.version == 6 and prefix.default_child_prefix_len and prefix.default_child_prefix_len > net.prefixlen:
        target_len = prefix.default_child_prefix_len
        # Obtener subredes hijas existentes
        stmt_children = select(IPAMPrefix.prefix).where(IPAMPrefix.parent_id == prefix.id)
        allocated_subnets = set((await db.execute(stmt_children)).scalars().all())

        for child in net.subnets(new_prefix=target_len):
            child_str = str(child)
            if child_str not in allocated_subnets:
                return IPAMPrefixNextAvailableResponse(
                    prefix_id=prefix.id,
                    next_available=child_str,
                    ip_family=IPFamilyEnum.IPv6,
                    is_subnet=True,
                    message=f"Siguiente subred delegada /{target_len} disponible",
                )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No hay subredes IPv6 disponibles en este bloque"
        )

    # Caso B: IPv4 o IPv6 para asignación de IPs de host
    stmt_allocated = select(IPAMAddress.address).where(
        IPAMAddress.prefix_id == prefix.id,
        IPAMAddress.status != IPAddressStatusEnum.DEPRECATED,
    )
    allocated_ips = set((await db.execute(stmt_allocated)).scalars().all())

    # Iterar hosts disponibles
    now = datetime.now(UTC)
    for host in net.hosts():
        # Representación en notación de host (/32 o /128)
        host_str = f"{host}/32" if net.version == 4 else f"{host}/128"
        host_ip = str(host)

        if host_str not in allocated_ips and host_ip not in allocated_ips:
            # Soft-lock de 5 minutos anti-colisión
            soft_locked_addr = IPAMAddress(
                tenant_id=tenant_id,
                prefix_id=prefix.id,
                address=host_str,
                ip_family=prefix.ip_family,
                status=IPAddressStatusEnum.SOFT_LOCKED,
                soft_lock_until=now + timedelta(minutes=5),
                description="Reserva temporal táctica en curso",
            )
            db.add(soft_locked_addr)
            await db.commit()

            return IPAMPrefixNextAvailableResponse(
                prefix_id=prefix.id,
                next_available=str(host),
                ip_family=prefix.ip_family,
                is_subnet=False,
                message="Dirección IP libre reservada temporalmente (Soft-Lock 5 min)",
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El bloque se encuentra al 100% de capacidad")


# ============================================================================
# 3. DIRECCIONES IP INDIVIDUALES
# ============================================================================
@router.get("/addresses", response_model=list[IPAMAddressResponse])
async def list_addresses(
    prefix_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[IPAddressStatusEnum] = Query(None),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista las direcciones IP asignadas o reservadas en el IPAM."""
    tenant_id = get_tenant_id(claims)
    stmt = select(IPAMAddress).where(IPAMAddress.tenant_id == tenant_id)
    if prefix_id:
        stmt = stmt.where(IPAMAddress.prefix_id == prefix_id)
    if status_filter:
        stmt = stmt.where(IPAMAddress.status == status_filter)

    stmt = stmt.order_by(IPAMAddress.address.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/addresses", response_model=IPAMAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: IPAMAddressCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)
    ),
) -> Any:
    """Asigna manualmente una dirección IP en el IPAM."""
    tenant_id = get_tenant_id(claims)

    # Normalizar dirección
    try:
        ip_iface = ipaddress.ip_interface(payload.address)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Dirección IP inválida: {e}"
        ) from e

    # Verificar si ya existe
    stmt_check = select(IPAMAddress).where(
        IPAMAddress.prefix_id == payload.prefix_id, IPAMAddress.address == str(ip_iface)
    )
    existing = (await db.execute(stmt_check)).scalar_one_or_none()
    if existing:
        if existing.status == IPAddressStatusEnum.SOFT_LOCKED:
            # Confirmar soft-lock a estado ALLOCATED
            existing.status = payload.status
            existing.router_id = payload.router_id
            existing.interface_name = payload.interface_name
            existing.mac_address = payload.mac_address
            existing.dns_ptr = payload.dns_ptr
            existing.description = payload.description
            existing.soft_lock_until = None
            await db.commit()
            await db.refresh(existing)
            return existing
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"La IP {ip_iface} ya está asignada")

    addr = IPAMAddress(
        tenant_id=tenant_id,
        prefix_id=payload.prefix_id,
        address=str(ip_iface),
        ip_family=payload.ip_family,
        status=payload.status,
        router_id=payload.router_id,
        interface_name=payload.interface_name,
        mac_address=payload.mac_address,
        dns_ptr=payload.dns_ptr,
        description=payload.description,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


# ============================================================================
# 4. SERVICIOS DE ABONADOS / CLIENTES
# ============================================================================
@router.get("/customer-services", response_model=list[CustomerServiceResponse])
async def list_customer_services(
    router_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[CustomerServiceStatusEnum] = Query(None),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista todos los abonados (PPPoE, DHCP o Estáticos) del ISP."""
    tenant_id = get_tenant_id(claims)
    stmt = select(CustomerService).where(CustomerService.tenant_id == tenant_id)
    if router_id:
        stmt = stmt.where(CustomerService.router_id == router_id)
    if status_filter:
        stmt = stmt.where(CustomerService.status == status_filter)

    stmt = stmt.order_by(CustomerService.endpoint_identifier.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/customer-services", response_model=CustomerServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_service(
    payload: CustomerServiceCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)
    ),
) -> Any:
    """Registra un nuevo servicio de cliente con su asignación IP Dual-Stack."""
    tenant_id = get_tenant_id(claims)

    endpoint_val = payload.endpoint_identifier or payload.pppoe_username
    # Si tiene endpoint/username, validar que no esté duplicado en el mismo router
    if endpoint_val:
        stmt_check = select(CustomerService).where(
            CustomerService.router_id == payload.router_id,
            CustomerService.endpoint_identifier == endpoint_val,
        )
        if (await db.execute(stmt_check)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El identificador de abonado '{endpoint_val}' ya existe en el router seleccionado",
            )

    svc = CustomerService(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        service_type=payload.service_type,
        auth_backend=payload.auth_backend,
        endpoint_identifier=endpoint_val,
        ipv4_address_id=payload.ipv4_address_id,
        ipv6_delegated_prefix=payload.ipv6_delegated_prefix,
        bandwidth_profile_id=payload.bandwidth_profile_id,
        onu_mode=payload.onu_mode,
        onu_mac_address=payload.onu_mac_address,
        device_serial=payload.device_serial or payload.onu_serial_number,
        cpe_wifi_mac_address=payload.cpe_wifi_mac_address,
        pon_port=payload.pon_port,
        optical_box=payload.optical_box,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=CustomerServiceStatusEnum.PENDING_INSTALL,
        last_reachability_status="ONLINE",
    )
    db.add(svc)
    await db.commit()
    await db.refresh(svc)

    await write_audit_log(
        session=db,
        tenant_id=tenant_id,
        actor_user_id=uuid.UUID(str(claims["sub"])),
        actor_username=str(claims.get("username", "system")),
        actor_role=claims.get("rol"),
        actor_ip="127.0.0.1",
        event_category="INVENTORY",
        event_action="CUSTOMER_SERVICE_CREATED",
        status_code=201,
        after_state={"customer_service_id": str(svc.id), "endpoint": svc.endpoint_identifier, "type": svc.service_type},
    )
    return svc


# ============================================================================
# 5. SINCRONIZACIÓN Y DESCUBRIMIENTO DESDE MIKROTIK
# ============================================================================
def _get_router_client(r: Router, tenant_id: uuid.UUID) -> MikrotikRestClient:
    """Obtiene un cliente REST configurado con credenciales descifradas de la bóveda o valores por defecto."""
    if r.vault:
        try:
            return _create_client_from_vault(r, tenant_id)
        except Exception as e:
            logger.warning(f"No se pudieron descifrar credenciales de bóveda para {r.display_name}: {e}")
    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    return MikrotikRestClient(host=host, port=r.api_port, username="admin", password="")


async def _sync_single_router_ipam(
    r: Router,
    tenant_id: uuid.UUID,
    db: AsyncSession,
    default_vrf: IPAMVrf,
) -> tuple[int, int]:
    """Sincroniza prefijos, pools, servidores DHCP y direcciones IP desde un router MikroTik."""
    synced_prefixes = 0
    synced_ips = 0

    client = _get_router_client(r, tenant_id)
    try:
        async with client:
            raw_addrs: list[dict[str, Any]] = []
            raw_pools: list[dict[str, Any]] = []
            raw_dhcp_servers: list[dict[str, Any]] = []
            raw_dhcp_networks: list[dict[str, Any]] = []
            raw_leases: list[dict[str, Any]] = []

            try:
                res = await client.get("/ip/address")
                if isinstance(res, list):
                    raw_addrs = res
            except Exception as e:
                logger.warning(f"Error consultando /ip/address en {r.display_name}: {e}")

            try:
                res = await client.get("/ip/pool")
                if isinstance(res, list):
                    raw_pools = res
            except Exception as e:
                logger.warning(f"Error consultando /ip/pool en {r.display_name}: {e}")

            try:
                res = await client.get("/ip/dhcp-server")
                if isinstance(res, list):
                    raw_dhcp_servers = res
            except Exception as e:
                logger.warning(f"Error consultando /ip/dhcp-server en {r.display_name}: {e}")

            try:
                res = await client.get("/ip/dhcp-server/network")
                if isinstance(res, list):
                    raw_dhcp_networks = res
            except Exception as e:
                logger.warning(f"Error consultando /ip/dhcp-server/network en {r.display_name}: {e}")

            try:
                res = await client.get("/ip/dhcp-server/lease")
                if isinstance(res, list):
                    raw_leases = res
            except Exception as e:
                logger.warning(f"Error consultando /ip/dhcp-server/lease en {r.display_name}: {e}")

            # Mapeos auxiliares de DHCP
            dhcp_net_map: dict[str, dict[str, Any]] = {}
            for net_item in raw_dhcp_networks:
                if isinstance(net_item, dict):
                    net_addr = net_item.get("address")
                    if net_addr:
                        dhcp_net_map[str(net_addr)] = net_item

            dhcp_srv_by_pool: dict[str, list[dict[str, Any]]] = {}
            for srv in raw_dhcp_servers:
                if isinstance(srv, dict):
                    p_name = srv.get("address-pool")
                    if p_name:
                        dhcp_srv_by_pool.setdefault(str(p_name), []).append(srv)

            # Cargar prefijos existentes de esta VRF en memoria
            known_prefixes: dict[str, IPAMPrefix] = {}
            stmt_pfx = select(IPAMPrefix).where(
                IPAMPrefix.tenant_id == tenant_id,
                IPAMPrefix.vrf_id == default_vrf.id,
            )
            for p in (await db.execute(stmt_pfx)).scalars().all():
                known_prefixes[str(p.prefix)] = p

            # 1. Procesar Pools de IPs (/ip/pool) y DHCP Networks
            for p_item in raw_pools:
                if not isinstance(p_item, dict):
                    continue
                pool_name = str(p_item.get("name", "") or "")
                ranges = str(p_item.get("ranges", "") or "")
                if not ranges:
                    continue

                first_range = ranges.split(",")[0].strip()
                start_ip_str = first_range.split("-")[0].strip()
                try:
                    start_ip = ipaddress.ip_address(start_ip_str)
                except ValueError:
                    continue

                matched_net_str: str | None = None
                for candidate_net_str in dhcp_net_map:
                    try:
                        cand_net = ipaddress.ip_network(candidate_net_str, strict=False)
                        if start_ip in cand_net:
                            matched_net_str = str(cand_net)
                            break
                    except ValueError:
                        continue

                if not matched_net_str:
                    for addr_item in raw_addrs:
                        if isinstance(addr_item, dict):
                            a_str = addr_item.get("address", "")
                            if a_str:
                                try:
                                    a_net = ipaddress.ip_interface(a_str).network
                                    if start_ip in a_net:
                                        matched_net_str = str(a_net)
                                        break
                                except ValueError:
                                    continue

                if not matched_net_str:
                    if start_ip.version == 4:
                        matched_net_str = f"{start_ip_str.rsplit('.', 1)[0]}.0/24"
                    else:
                        continue

                # Calcular utilización
                try:
                    total = int(p_item.get("total", 0) or 0)
                    used = int(p_item.get("used", 0) or 0)
                    util_pct = Decimal(str(round((used / total) * 100, 2))) if total > 0 else Decimal("0.00")
                except (ValueError, TypeError):
                    util_pct = Decimal("0.00")

                srv_list = dhcp_srv_by_pool.get(pool_name, [])
                srv_names = ", ".join(s.get("name", "") for s in srv_list) if srv_list else "Sin DHCP Server"
                srv_ifaces = ", ".join(s.get("interface", "") for s in srv_list if s.get("interface"))

                desc = f"Pool: {pool_name} ({ranges}) • DHCP: {srv_names}"
                if srv_ifaces:
                    desc += f" en {srv_ifaces}"
                desc += f" • Router: {r.display_name}"

                if matched_net_str in known_prefixes:
                    prefix = known_prefixes[matched_net_str]
                    prefix.is_pool = True
                    prefix.role = IPPrefixRoleEnum.CUSTOMER_RESIDENTIAL
                    prefix.utilization_pct = util_pct
                    prefix.description = desc
                    prefix.status = IPPrefixStatusEnum.ACTIVE
                else:
                    prefix = IPAMPrefix(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        vrf_id=default_vrf.id,
                        prefix=matched_net_str,
                        ip_family=IPFamilyEnum.IPv4 if start_ip.version == 4 else IPFamilyEnum.IPv6,
                        role=IPPrefixRoleEnum.CUSTOMER_RESIDENTIAL,
                        status=IPPrefixStatusEnum.ACTIVE,
                        is_pool=True,
                        utilization_pct=util_pct,
                        description=desc,
                    )
                    db.add(prefix)
                    if hasattr(db, "flush") and callable(db.flush):
                        await db.flush()
                    known_prefixes[matched_net_str] = prefix
                    synced_prefixes += 1

            # 2. Procesar Interfaces IP (/ip/address)
            for item in raw_addrs:
                if not isinstance(item, dict):
                    continue
                ip_str = item.get("address", "")
                if not ip_str:
                    continue
                try:
                    iface_net = ipaddress.ip_interface(ip_str)
                    net_str = str(iface_net.network)
                    if net_str not in known_prefixes:
                        role = IPPrefixRoleEnum.MGMT if item.get("interface") == "ether1" else IPPrefixRoleEnum.INFRA_P2P
                        prefix = IPAMPrefix(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            vrf_id=default_vrf.id,
                            prefix=net_str,
                            ip_family=IPFamilyEnum.IPv4 if iface_net.version == 4 else IPFamilyEnum.IPv6,
                            role=role,
                            status=IPPrefixStatusEnum.ACTIVE,
                            is_pool=False,
                            utilization_pct=Decimal("0.00"),
                            description=f"Interfaz {item.get('interface', '')} ({r.display_name})",
                        )
                        db.add(prefix)
                        if hasattr(db, "flush") and callable(db.flush):
                            await db.flush()
                        known_prefixes[net_str] = prefix
                        synced_prefixes += 1
                    else:
                        prefix = known_prefixes[net_str]

                    stmt_addr = select(IPAMAddress).where(
                        IPAMAddress.prefix_id == prefix.id,
                        IPAMAddress.address == str(iface_net.ip),
                    )
                    addr_row = (await db.execute(stmt_addr)).scalar_one_or_none()
                    if not addr_row:
                        addr_row = IPAMAddress(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            prefix_id=prefix.id,
                            address=str(iface_net.ip),
                            ip_family=IPFamilyEnum.IPv4 if iface_net.version == 4 else IPFamilyEnum.IPv6,
                            router_id=r.id,
                            interface_name=item.get("interface"),
                            status=IPAddressStatusEnum.ALLOCATED,
                            description=f"Gateway/Interfaz {item.get('interface', '')} ({item.get('comment') or r.display_name})",
                        )
                        db.add(addr_row)
                        synced_ips += 1
                    else:
                        addr_row.status = IPAddressStatusEnum.ALLOCATED
                        addr_row.router_id = r.id
                        addr_row.interface_name = item.get("interface")
                except Exception as ex:
                    logger.warning(f"Error procesando /ip/address {ip_str}: {ex}")

            # 3. Procesar Leases de DHCP (/ip/dhcp-server/lease)
            for lease in raw_leases:
                if not isinstance(lease, dict):
                    continue
                l_ip = lease.get("active-address") or lease.get("address")
                if not l_ip:
                    continue
                try:
                    clean_ip = str(l_ip).split("/")[0].strip()
                    ip_obj = ipaddress.ip_address(clean_ip)
                    clean_ip_str = str(ip_obj)
                    target_pfx: IPAMPrefix | None = None
                    for net_str, pfx in known_prefixes.items():
                        try:
                            if ip_obj in ipaddress.ip_network(net_str, strict=False):
                                target_pfx = pfx
                                break
                        except ValueError:
                            continue

                    if not target_pfx:
                        continue

                    mac = lease.get("mac-address") or lease.get("active-mac-address") or lease.get("src-mac-address")
                    hostname = lease.get("host-name")
                    is_dynamic = lease.get("dynamic") != "false"
                    lease_status = IPAddressStatusEnum.DHCP_DYNAMIC if is_dynamic else IPAddressStatusEnum.DHCP_STATIC

                    stmt_l = select(IPAMAddress).where(
                        IPAMAddress.prefix_id == target_pfx.id,
                        IPAMAddress.address == clean_ip_str,
                    )
                    lease_row = (await db.execute(stmt_l)).scalar_one_or_none()
                    if not lease_row:
                        lease_row = IPAMAddress(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            prefix_id=target_pfx.id,
                            address=clean_ip_str,
                            ip_family=IPFamilyEnum.IPv4 if ip_obj.version == 4 else IPFamilyEnum.IPv6,
                            router_id=r.id,
                            interface_name=lease.get("server"),
                            mac_address=str(mac)[:17] if mac else None,
                            dns_ptr=str(hostname)[:255] if hostname else None,
                            status=lease_status,
                            description=f"DHCP: {hostname or 'Cliente'} | Mac: {mac or 'N/A'} | Srv: {lease.get('server', '')}",
                        )

                        db.add(lease_row)
                        synced_ips += 1
                    else:
                        lease_row.status = lease_status
                        lease_row.mac_address = str(mac)[:17] if mac else lease_row.mac_address
                        lease_row.dns_ptr = str(hostname)[:255] if hostname else lease_row.dns_ptr
                        lease_row.router_id = r.id
                except Exception as ex:
                    logger.warning(f"Error procesando lease {l_ip}: {ex}")

            await db.commit()

    except Exception as e:
        logger.warning(f"Error sincronizando IPAM desde {r.display_name}: {e}")

    return synced_prefixes, synced_ips


async def _sync_all_tenant_routers_ipam(tenant_id: uuid.UUID, db: AsyncSession) -> tuple[int, int]:
    """Sincroniza todos los routers alcanzables del tenant."""
    stmt_vrf = select(IPAMVrf).where(IPAMVrf.tenant_id == tenant_id, IPAMVrf.name == "default")
    default_vrf = (await db.execute(stmt_vrf)).scalar_one_or_none()
    if not default_vrf:
        default_vrf = IPAMVrf(tenant_id=tenant_id, name="default", description="VRF Global de Enrutamiento")
        db.add(default_vrf)
        await db.commit()
        await db.refresh(default_vrf)

    stmt_routers = (
        select(Router)
        .where(Router.tenant_id == tenant_id, Router.is_reachable == True)  # noqa: E712
        .options(selectinload(Router.vault))
    )
    routers = (await db.execute(stmt_routers)).scalars().all()

    total_pfx = 0
    total_ips = 0
    for r in routers:
        p, i = await _sync_single_router_ipam(r, tenant_id, db, default_vrf)
        total_pfx += p
        total_ips += i

    return total_pfx, total_ips


@router.post("/sync-all", status_code=status.HTTP_200_OK)
async def sync_all_mikrotik_ipam(
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> Any:
    """Descubre y sincroniza prefijos, pools y DHCP de todos los routers alcanzables del tenant."""
    tenant_id = get_tenant_id(claims)
    pfx_count, ips_count = await _sync_all_tenant_routers_ipam(tenant_id, db)
    stmt = select(func.count(Router.id)).where(Router.tenant_id == tenant_id)
    val = (await db.execute(stmt)).scalar()
    routers_total = int(val) if isinstance(val, (int, float)) else (1 if val is not None else 0)
    return {
        "status": "success",
        "synced_prefixes": pfx_count,
        "synced_ips": ips_count,
        "routers_processed": routers_total,
        "message": f"Sincronización masiva completada: {pfx_count} prefijos y {ips_count} IPs descubiertas en {routers_total} routers de la flota",
    }




@router.post("/sync-mikrotik/{router_id}", status_code=status.HTTP_200_OK)
async def sync_mikrotik_ipam(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> Any:
    """Descubre subredes, pools y servidores DHCP configurados en el router MikroTik y las sincroniza con el IPAM."""
    tenant_id = get_tenant_id(claims)
    stmt = (
        select(Router)
        .where(Router.id == router_id, Router.tenant_id == tenant_id)
        .options(selectinload(Router.vault))
    )
    r = (await db.execute(stmt)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")

    # Asegurar VRF por defecto
    stmt_vrf = select(IPAMVrf).where(IPAMVrf.tenant_id == tenant_id, IPAMVrf.name == "default")
    default_vrf = (await db.execute(stmt_vrf)).scalar_one_or_none()
    if not default_vrf:
        default_vrf = IPAMVrf(tenant_id=tenant_id, name="default", description="VRF Global de Enrutamiento")
        db.add(default_vrf)
        await db.commit()
        await db.refresh(default_vrf)

    synced_prefixes, synced_ips = await _sync_single_router_ipam(r, tenant_id, db, default_vrf)

    return {
        "status": "success",
        "router_id": str(r.id),
        "synced_prefixes": synced_prefixes,
        "synced_ips": synced_ips,
        "message": f"Sincronización completada: {synced_prefixes} prefijos y {synced_ips} IPs procesadas",
    }
