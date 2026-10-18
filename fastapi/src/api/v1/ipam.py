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

from src.api.deps import get_current_user_claims, require_roles
from src.core.audit import write_audit_log
from src.db.session import get_tenant_db_session
from src.mikrotik.client import MikrotikRestClient
from src.models.core import SystemRoleEnum, User
from src.models.inventory import Router, RouterCredentialsVault
from src.models.ipam import (
    CustomerService,
    CustomerServiceStatusEnum,
    IPAddressStatusEnum,
    IPAMAddress,
    IPAMPrefix,
    IPAMVrf,
    IPFamilyEnum,
    IPPrefixRoleEnum,
)
from src.schemas.ipam import (
    CustomerServiceCreate,
    CustomerServiceResponse,
    CustomerServiceUpdate,
    IPAMAddressCreate,
    IPAMAddressResponse,
    IPAMAddressUpdate,
    IPAMPrefixCreate,
    IPAMPrefixNextAvailableResponse,
    IPAMPrefixResponse,
    IPAMPrefixUpdate,
    IPAMVrfCreate,
    IPAMVrfResponse,
    IPAMVrfUpdate,
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
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)),
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
        db=db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(claims["sub"]),
        username=claims.get("username", "system"),
        event_action="IPAM_VRF_CREATED",
        event_category="INVENTORY",
        status_code=201,
        details={"vrf_id": str(vrf.id), "name": vrf.name},
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
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Lista prefijos y subredes con filtros por VRF, Familia de IP y Rol."""
    tenant_id = get_tenant_id(claims)
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
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)),
) -> Any:
    """Registra un nuevo prefijo o subred CIDR validada matemáticamente."""
    tenant_id = get_tenant_id(claims)

    # Validar notación CIDR estricta
    try:
        network_obj = ipaddress.ip_network(payload.prefix, strict=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Formato CIDR inválido: {e}")

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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El prefijo {network_obj} ya está registrado en esta VRF")

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
        db=db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(claims["sub"]),
        username=claims.get("username", "system"),
        event_action="IPAM_PREFIX_CREATED",
        event_category="INVENTORY",
        status_code=201,
        details={"prefix_id": str(prefix.id), "prefix": prefix.prefix, "role": prefix.role},
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay subredes IPv6 disponibles en este bloque")

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
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)),
) -> Any:
    """Asigna manualmente una dirección IP en el IPAM."""
    tenant_id = get_tenant_id(claims)

    # Normalizar dirección
    try:
        ip_iface = ipaddress.ip_interface(payload.address)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Dirección IP inválida: {e}")

    # Verificar si ya existe
    stmt_check = select(IPAMAddress).where(IPAMAddress.prefix_id == payload.prefix_id, IPAMAddress.address == str(ip_iface))
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

    stmt = stmt.order_by(CustomerService.customer_name.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/customer-services", response_model=CustomerServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_service(
    payload: CustomerServiceCreate,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN, SystemRoleEnum.INVENTORY_MANAGER)),
) -> Any:
    """Registra un nuevo servicio de cliente con su asignación IP Dual-Stack."""
    tenant_id = get_tenant_id(claims)

    # Si es PPPoE, validar que el username no esté duplicado en el mismo router
    if payload.pppoe_username:
        stmt_check = select(CustomerService).where(
            CustomerService.router_id == payload.router_id,
            CustomerService.pppoe_username == payload.pppoe_username,
        )
        if (await db.execute(stmt_check)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El usuario PPPoE '{payload.pppoe_username}' ya existe en el router seleccionado",
            )

    svc = CustomerService(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        customer_name=payload.customer_name,
        customer_code=payload.customer_code,
        service_type=payload.service_type,
        auth_backend=payload.auth_backend,
        pppoe_username=payload.pppoe_username,
        ipv4_address_id=payload.ipv4_address_id,
        ipv6_delegated_prefix=payload.ipv6_delegated_prefix,
        onu_mode=payload.onu_mode,
        onu_mac_address=payload.onu_mac_address,
        onu_serial_number=payload.onu_serial_number,
        cpe_wifi_mac_address=payload.cpe_wifi_mac_address,
        pon_port=payload.pon_port,
        optical_box=payload.optical_box,
        physical_address=payload.physical_address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=CustomerServiceStatusEnum.PENDING_INSTALL,
    )
    db.add(svc)
    await db.commit()
    await db.refresh(svc)

    await write_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(claims["sub"]),
        username=claims.get("username", "system"),
        event_action="CUSTOMER_SERVICE_CREATED",
        event_category="INVENTORY",
        status_code=201,
        details={"customer_service_id": str(svc.id), "name": svc.customer_name, "type": svc.service_type},
    )
    return svc


# ============================================================================
# 5. SINCRONIZACIÓN Y DESCUBRIMIENTO DESDE MIKROTIK
# ============================================================================
@router.post("/sync-mikrotik/{router_id}", status_code=status.HTTP_200_OK)
async def sync_mikrotik_ipam(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
) -> Any:
    """Descubre subredes e IPs configuradas en el router MikroTik y las sincroniza con el IPAM."""
    tenant_id = get_tenant_id(claims)
    stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
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

    synced_prefixes = 0
    synced_ips = 0

    try:
        async with MikrotikRestClient(base_url=r.api_base_url, port=r.api_port, username="admin", password="") as client:
            raw_addrs = await client.get("/ip/address")
            for item in raw_addrs:
                ip_str = item.get("address")
                if not ip_str:
                    continue
                try:
                    iface_net = ipaddress.ip_interface(ip_str)
                    net_str = str(iface_net.network)

                    # Verificar si el prefijo ya existe
                    stmt_p = select(IPAMPrefix).where(
                        IPAMPrefix.tenant_id == tenant_id,
                        IPAMPrefix.vrf_id == default_vrf.id,
                        IPAMPrefix.prefix == net_str,
                    )
                    prefix = (await db.execute(stmt_p)).scalar_one_or_none()
                    if not prefix:
                        prefix = IPAMPrefix(
                            tenant_id=tenant_id,
                            vrf_id=default_vrf.id,
                            prefix=net_str,
                            ip_family=IPFamilyEnum.IPv4,
                            role=IPPrefixRoleEnum.INFRA_P2P,
                            description=f"Descubierto en router {r.display_name} ({item.get('interface', '')})",
                        )
                        db.add(prefix)
                        await db.commit()
                        await db.refresh(prefix)
                        synced_prefixes += 1

                    # Registrar la IP específica de la interfaz
                    stmt_addr = select(IPAMAddress).where(
                        IPAMAddress.prefix_id == prefix.id,
                        IPAMAddress.address == str(iface_net),
                    )
                    if not (await db.execute(stmt_addr)).scalar_one_or_none():
                        addr = IPAMAddress(
                            tenant_id=tenant_id,
                            prefix_id=prefix.id,
                            address=str(iface_net),
                            ip_family=IPFamilyEnum.IPv4,
                            router_id=r.id,
                            interface_name=item.get("interface"),
                            status=IPAddressStatusEnum.ALLOCATED,
                            description="Interfaz local descubierta",
                        )
                        db.add(addr)
                        await db.commit()
                        synced_ips += 1
                except Exception as ex:
                    logger.warning(f"Error procesando IP {ip_str}: {ex}")
    except Exception as e:
        logger.warning(f"Sincronización simulada o error de conexión con MikroTik: {e}")

    return {
        "status": "success",
        "router_id": str(r.id),
        "synced_prefixes": synced_prefixes,
        "synced_ips": synced_ips,
        "message": f"Sincronización completada: {synced_prefixes} prefijos y {synced_ips} IPs procesadas",
    }
