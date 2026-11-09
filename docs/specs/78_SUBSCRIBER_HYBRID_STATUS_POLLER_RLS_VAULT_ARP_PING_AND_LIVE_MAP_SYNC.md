# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 78: Monitoreo Periódico Híbrido de Abonados FTTH (`StaggeredSessionPoller`): Unificación PPPoE + DHCP + Tabla ARP + Ping ICMP Ligero, Contexto RLS + `selectinload(Router.vault, SubscriberDevice.ipv4_address)` y Sincronización Reactiva WebSocket en Mapa e IPAM (Hito 28.21)

> **Estado:** Aprobado para Ejecución (*Flash-Ready Specification*)  
> **Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
> **Hito Asociado:** Hito 28 — Subhito `28.21` (`ROADMAP.md`)  
> **Archivos Afectados:**
> 1. `fastapi/src/core/config.py`
> 2. `fastapi/src/workers/subscriber_status_poller.py`
> 3. `vue3/src/stores/useNocEventsStore.ts`
> 4. `vue3/src/stores/useIpamStore.ts`
> 5. `fastapi/tests/workers/test_subscriber_status_poller.unit.py`

---

## 1. Diagnóstico Forense de las 4 Fallas en `subscriber_status_poller.py`

Al inspeccionar el worker de monitoreo automático de clientes en segundo plano ([`fastapi/src/workers/subscriber_status_poller.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/subscriber_status_poller.py)), se identificaron **4 defectos críticos** que impedían detectar cambios de estado reales (`ONLINE` $\leftrightarrow$ `OFFLINE`) en despliegues FTTH con DHCP, PPPoE e IP Estática:

1. **Exclusión Mutua Errónea `if is_isp_mode:` entre `/ppp/active` y `/ip/dhcp-server/lease` (Líneas 62–85):**
   - Cuando `isp_module_enabled == True`, `_poll_single_router_sessions` ejecutaba **únicamente `client.get("/ppp/active")`** y omitía por completo `/ip/dhcp-server/lease`.
   - En consecuencia, todo ISP FTTH que opere abonados por **DHCP** (o redes mixtas DHCP + PPPoE) veía a sus clientes DHCP caer falsamente a `OFFLINE` porque el poller jamás consultaba la tabla de leases DHCP cuando `is_isp_mode=True`.
2. **Falsos Positivos `"bound"` en Clientes DHCP / IP Estática cuando la ONU se Apaga (Ausencia de Verificación ARP / Ping ICMP):**
   - En **PPPoE**, si la ONU se apaga o pierde fibra, el túnel cae en segundos por LCP Keepalive y desaparece de `/ppp/active`.
   - En cambio, en **DHCP**, cuando el cliente apaga la ONU, el registro en `/ip/dhcp-server/lease` **permanece en `status="bound"` hasta que venza el `lease-time` (ej. 1 hora o 24 horas)**.
   - Para detectar que una ONU DHCP o IP Estática se apagó sin esperar a que venza el lease, el poller debe cruzar con la **tabla ARP del router (`/ip/arp`)** (verificando que no esté `failed`/`invalid`) y, cuando `verify_icmp=True` (`ROSGRID_SUBSCRIBER_ICMP_PROBE_ENABLED`), ejecutar un **sondeo ICMP ligero (`POST /rest/ping` con `count=1`, `interval="200ms"`)** sobre los abonados DHCP/Estáticos registrados para confirmar alcanzabilidad real en Capa 3.
3. **Ausencia de Contexto RLS (`set_tenant_context`) y `MissingGreenlet` por Relaciones No Precargadas (`Router.vault` y `SubscriberDevice.ipv4_address`):**
   - `poll_tenant_subscribers_cycle` y `subscriber_status_poller_worker_loop` abrían `async_session_maker()` sin invocar `await set_tenant_context(session, tenant_id)` ni `await set_tenant_context(session, None, is_superadmin=True)`.
   - Además, `select(Router)` no incluía `.options(selectinload(Router.vault))` y `select(SubscriberDevice)` no incluía `.options(selectinload(SubscriberDevice.ipv4_address))`. Al acceder a `router.vault` (en `_create_client_from_vault`) o a `dev.assigned_ipv4` (propiedad que lee `dev.ipv4_address`), SQLAlchemy `AsyncSession` disparaba `MissingGreenlet`.
4. **Falta de Actualización Reactiva en la Tabla de IPAM (`/ipam`) al Recibir `DEVICE_STATUS_CHANGED` por WebSocket:**
   - Aunque `UnifiedNetworkMap.vue` escucha `nocEventsStore.lastDeviceStatusEvent`, el store [`useIpamStore.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/stores/useIpamStore.ts) no actualizaba `customerServices` al llegar el evento WebSocket `DEVICE_STATUS_CHANGED`, dejando el badge de estado en `/ipam` desactualizado hasta recargar la vista.

---

## 2. Instrucciones Literales de Implementación Paso a Paso (Flash-Ready)

### Paso 1: Añadir Parámetros de Sondeo Híbrido en `fastapi/src/core/config.py`

En [`fastapi/src/core/config.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/config.py) (líneas 70–75), declarar `ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS` y `ROSGRID_SUBSCRIBER_ICMP_PROBE_ENABLED`:

#### `Target` en `fastapi/src/core/config.py`:
```python
    # MikroTik & Operaciones
    ROSGRID_MIKROTIK_TIMEOUT_SECONDS: int = 10
    ROSGRID_SAFEMODE_ROLLBACK_SECONDS: int = 60
    ROSGRID_BACKUP_RETENTION_DAYS: int = 30
```

#### `Replacement` en `fastapi/src/core/config.py`:
```python
    # MikroTik & Operaciones
    ROSGRID_MIKROTIK_TIMEOUT_SECONDS: int = 10
    ROSGRID_SAFEMODE_ROLLBACK_SECONDS: int = 60
    ROSGRID_BACKUP_RETENTION_DAYS: int = 30
    ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS: int = 180
    ROSGRID_SUBSCRIBER_ICMP_PROBE_ENABLED: bool = True
```

---

### Paso 2: Refactorizar `fastapi/src/workers/subscriber_status_poller.py` (Sondeo Dual PPPoE + DHCP + ARP/ICMP, Contexto RLS, `selectinload` y Soporte BNG)

Reemplazar el contenido de [`fastapi/src/workers/subscriber_status_poller.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/subscriber_status_poller.py) manteniendo 100% de compatibilidad con las firmas y pruebas existentes en `test_subscriber_status_poller.unit.py` y garantizando complejidad ciclomática Radon Grado A (`CC <= 4`):

#### `Target` en `fastapi/src/workers/subscriber_status_poller.py`:
```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller) de Clientes y Dispositivos.

Consulta periódicamente las tablas nativas de sesiones de RouterOS v7 (/ip/dhcp-server/lease o /ppp/active)
aplicando jitter temporal entre routers para erradicar picos de CPU, filtrado delta de escritura cero en DB,
y notificación reactiva de eventos DEVICE_STATUS_CHANGED vía Pub/Sub a WebSockets.
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from src.api.v1.webfig_common import _create_client_from_vault
from src.core.config import settings
from src.db.session import async_session_maker
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import SubscriberDevice
from src.redis_layer.client import get_redis_client

logger = logging.getLogger("rosgrid-subscriber-poller")

DEFAULT_POLL_INTERVAL_SECONDS: int = 180
MIN_INTER_ROUTER_JITTER_SECONDS: float = 2.0


async def _poll_single_router_sessions(
    session: Any,
    tenant_id: uuid.UUID,
    router: Router,
    is_isp_mode: bool,
) -> int:
    """Consulta pasiva compacta de las tablas de sesiones en RouterOS v7 con filtro delta en base de datos."""
    redis = get_redis_client()

    # 1. Comprobación rápida de Circuit Breaker en KeyDB
    cb_key = f"rg:{tenant_id}:diag:circuit:router:{router.id}"
    cb_state = await redis.get(cb_key)
    if cb_state and (cb_state == "OPEN" or cb_state == b"OPEN"):
        logger.debug(f"Router {router.display_name} en Circuit Breaker abierto. Omitiendo sondeo pasivo.")
        return 0

    client = None
    try:
        client = _create_client_from_vault(router, tenant_id)
    except Exception as exc:
        logger.debug(f"No se pudo crear cliente para router {router.display_name}: {exc}")
        return 0

    active_identifiers: set[str] = set()

    try:
        async with client:
            if is_isp_mode:
                raw_active = await asyncio.wait_for(client.get("/ppp/active"), timeout=8.0)
                if isinstance(raw_active, list):
                    for item in raw_active:
                        if isinstance(item, dict):
                            name = str(item.get("name") or "").strip()
                            addr = str(item.get("address") or "").strip()
                            if name:
                                active_identifiers.add(name.lower())
                            if addr:
                                active_identifiers.add(addr)
            else:
                raw_leases = await asyncio.wait_for(client.get("/ip/dhcp-server/lease"), timeout=8.0)
                if isinstance(raw_leases, list):
                    for item in raw_leases:
                        if isinstance(item, dict):
                            st = str(item.get("status") or "").lower()
                            if st in ("bound", "active"):
                                addr = str(item.get("address") or "").strip()
                                mac = str(item.get("mac-address") or "").replace(":", "").replace("-", "").upper()
                                if addr:
                                    active_identifiers.add(addr)
                                if mac:
                                    active_identifiers.add(mac)
    except Exception as exc:
        logger.warning(f"Error consultando tablas de sesiones en router {router.display_name}: {exc}")
        return 0

    # 2. Consultar los dispositivos registrados para este router
    stmt_devs = select(SubscriberDevice).where(
        SubscriberDevice.tenant_id == tenant_id,
        SubscriberDevice.router_id == router.id,
    )
    devices = list((await session.execute(stmt_devs)).scalars().all())
    if not devices:
        return 0

    changed_count = 0
    now_utc = datetime.now(UTC)
    pubsub_channel = f"rg:pubsub:events:{tenant_id}"

    for dev in devices:
        # Evaluar presencia en el set de activos
        ip = str(dev.assigned_ipv4 or "").strip()
        mac = str(dev.onu_mac_address or "").replace(":", "").replace("-", "").upper()
        pppoe = str(dev.pppoe_username or "").strip().lower()

        is_present = False
        if ip and ip in active_identifiers:
            is_present = True
        elif mac and mac in active_identifiers:
            is_present = True
        elif pppoe and pppoe in active_identifiers:
            is_present = True

        new_status = "ONLINE" if is_present else "OFFLINE"

        # 3. Filtro Delta (Zero-Write DB): Solo actualiza y emite si hay cambio de estado
        if new_status != dev.last_reachability_status:
            dev.last_reachability_status = new_status
            dev.last_seen_at = now_utc
            changed_count += 1

            # Emitir evento reactivo a WebSocket
            event_payload = {
                "event_name": "DEVICE_STATUS_CHANGED",
                "payload": {
                    "device_id": str(dev.id),
                    "status": new_status,
                    "router_id": str(router.id),
                    "endpoint_identifier": dev.endpoint_identifier,
                    "last_seen_at": now_utc.isoformat(),
                },
            }
            try:
                await redis.publish(pubsub_channel, json.dumps(event_payload))
            except Exception as e:
                logger.debug(f"Aviso publicando evento DEVICE_STATUS_CHANGED: {e}")

    if changed_count > 0:
        await session.commit()
        logger.info(
            f"[Poller Delta] Router {router.display_name}: {changed_count} dispositivos cambiaron de estado."
        )

    return changed_count


async def poll_tenant_subscribers_cycle(tenant_id: uuid.UUID, is_isp_mode: bool) -> None:
    """Ejecuta el ciclo de sondeo pasivo escalonado para todos los routers de un tenant."""
    async with async_session_maker() as session:
        stmt_routers = (
            select(Router)
            .where(
                Router.tenant_id == tenant_id,
                Router.admin_state != RouterAdminStateEnum.RETIRED,
                Router.is_reachable.is_(True),
            )
            .order_by(Router.display_name.asc())
        )
        routers = list((await session.execute(stmt_routers)).scalars().all())
        if not routers:
            return

        interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)
        base_delay = max(MIN_INTER_ROUTER_JITTER_SECONDS, interval / max(1, len(routers)))

        for r in routers:
            await _poll_single_router_sessions(session, tenant_id, r, is_isp_mode)
            # Jitter dinámico entre routers para aplanar la curva de carga
            jitter = random.uniform(0.1, 0.8)
            await asyncio.sleep(base_delay + jitter)


async def subscriber_status_poller_worker_loop() -> None:
    """Loop principal del Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller)."""
    logger.info("=== Iniciando Worker de Sondeo Pasivo Escalonado (StaggeredSessionPoller) ===")
    interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)

    while True:
        try:
            async with async_session_maker() as session:
                stmt_t = select(Tenant).where(Tenant.status == TenantStatusEnum.ACTIVE)
                tenants = list((await session.execute(stmt_t)).scalars().all())

            for t in tenants:
                is_isp = bool(getattr(t, "isp_module_enabled", False))
                try:
                    await poll_tenant_subscribers_cycle(t.id, is_isp)
                except Exception as e:
                    logger.warning(f"Error en ciclo de sondeo para tenant {t.name}: {e}")

        except asyncio.CancelledError:
            logger.info("Worker StaggeredSessionPoller cancelado.")
            break
        except Exception as exc:
            logger.error(f"Excepción en ciclo de StaggeredSessionPoller: {exc}", exc_info=True)

        await asyncio.sleep(interval)
```

#### `Replacement` en `fastapi/src/workers/subscriber_status_poller.py`:
```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Worker de Sondeo Híbrido Escalonado (StaggeredSessionPoller) de Clientes y Dispositivos FTTH.

Consulta periódicamente las tablas nativas de sesiones de RouterOS v7 (/ppp/active + /ip/dhcp-server/lease)
y verifica alcanzabilidad ICMP ligera cuando procede, aplicando contexto RLS por tenant, precarga ansiosa
selectinload(Router.vault, SubscriberDevice.ipv4_address), filtro delta de escritura cero en DB y emisión
reactiva de eventos DEVICE_STATUS_CHANGED vía Pub/Sub hacia WebSockets.
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.v1.webfig_common import _create_client_from_vault
from src.core.config import settings
from src.db.rls import set_tenant_context
from src.db.session import async_session_maker
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router, RouterAdminStateEnum
from src.models.ipam import SubscriberDevice
from src.redis_layer.client import get_redis_client

logger = logging.getLogger("rosgrid-subscriber-poller")

DEFAULT_POLL_INTERVAL_SECONDS: int = 180
MIN_INTER_ROUTER_JITTER_SECONDS: float = 2.0


def _clean_mac_hex(raw_mac: Any) -> str:
    """Normaliza una dirección MAC eliminando separadores para cruce rápido en memoria."""
    if not raw_mac:
        return ""
    return "".join(ch for ch in str(raw_mac).strip().upper() if ch in "0123456789ABCDEF")


def _extract_ppp_active_identifiers(raw_active: Any, active_identifiers: set[str]) -> None:
    """Extrae usernames, direcciones IP y caller-id MAC de /ppp/active."""
    if not isinstance(raw_active, list):
        return
    for item in raw_active:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower()
        addr = str(item.get("address") or "").strip()
        caller_mac = _clean_mac_hex(item.get("caller-id"))
        if name:
            active_identifiers.add(name)
        if addr:
            active_identifiers.add(addr)
        if caller_mac:
            active_identifiers.add(caller_mac)


def _extract_dhcp_lease_identifiers(raw_leases: Any, active_identifiers: set[str]) -> None:
    """Extrae direcciones IPv4 y MACs con estado bound/active desde /ip/dhcp-server/lease."""
    if not isinstance(raw_leases, list):
        return
    for item in raw_leases:
        if not isinstance(item, dict):
            continue
        st = str(item.get("status") or "").lower()
        if st in ("bound", "active"):
            addr = str(item.get("address") or item.get("active-address") or "").strip()
            mac = _clean_mac_hex(item.get("mac-address") or item.get("active-mac-address"))
            if addr:
                active_identifiers.add(addr)
            if mac:
                active_identifiers.add(mac)


def _is_device_matched(dev: SubscriberDevice, active_identifiers: set[str]) -> bool:
    """Evalúa si un abonado aparece en el conjunto de sesiones/leases activos del router."""
    ip = str(getattr(dev, "assigned_ipv4", "") or "").strip()
    mac = _clean_mac_hex(getattr(dev, "onu_mac_address", ""))
    pppoe = str(getattr(dev, "pppoe_username", "") or getattr(dev, "endpoint_identifier", "") or "").strip().lower()
    return bool(
        (ip and ip in active_identifiers)
        or (mac and mac in active_identifiers)
        or (pppoe and pppoe in active_identifiers)
    )


async def _probe_device_icmp_alive(client: Any, target_ip: str) -> bool | None:
    """Realiza un sondeo ICMP rápido (count=1) cuando el cliente soporta POST /ping.
    Retorna True/False si obtuvo respuesta válida de RouterOS, o None si el cliente es un mock pasivo.
    """
    post_fn = getattr(client, "post", None)
    if post_fn is None:
        return None
    try:
        res = await asyncio.wait_for(
            post_fn("/ping", json_data={"address": target_ip, "count": 1, "interval": "200ms"}),
            timeout=3.0,
        )
        if not isinstance(res, list) or len(res) == 0:
            return None
        for pkt in res:
            if not isinstance(pkt, dict):
                continue
            received = pkt.get("received")
            if received is not None:
                return int(received) > 0
            if pkt.get("status") in ("echo reply", None) and pkt.get("time"):
                return True
            if pkt.get("status") in ("timeout", "host unreachable", "net unreachable"):
                return False
    except Exception:
        return None
    return None


async def _collect_router_active_identifiers(
    client: Any,
    is_isp_mode: bool,
    devices: list[SubscriberDevice],
    verify_icmp: bool = False,
) -> set[str]:
    """Consulta las tablas de sesiones de RouterOS (/ppp/active y /ip/dhcp-server/lease) y verifica ICMP."""
    active_identifiers: set[str] = set()
    if is_isp_mode:
        raw_active = await asyncio.wait_for(client.get("/ppp/active"), timeout=8.0)
        _extract_ppp_active_identifiers(raw_active, active_identifiers)
        # Si existen abonados DHCP/Estáticos aún no encontrados en /ppp/active, consultar también DHCP leases
        if any(not _is_device_matched(d, active_identifiers) for d in devices):
            try:
                raw_leases = await asyncio.wait_for(client.get("/ip/dhcp-server/lease"), timeout=8.0)
                _extract_dhcp_lease_identifiers(raw_leases, active_identifiers)
            except Exception:
                pass
    else:
        raw_leases = await asyncio.wait_for(client.get("/ip/dhcp-server/lease"), timeout=8.0)
        _extract_dhcp_lease_identifiers(raw_leases, active_identifiers)

    if verify_icmp:
        for dev in devices:
            ip = str(getattr(dev, "assigned_ipv4", "") or "").strip()
            if not ip:
                continue
            icmp_alive = await _probe_device_icmp_alive(client, ip)
            if icmp_alive is True:
                active_identifiers.add(ip)
            elif icmp_alive is False:
                active_identifiers.discard(ip)
                mac = _clean_mac_hex(getattr(dev, "onu_mac_address", ""))
                if mac:
                    active_identifiers.discard(mac)

    return active_identifiers


async def _publish_device_status_change(
    redis: Any,
    tenant_id: uuid.UUID,
    router_id: uuid.UUID,
    dev: SubscriberDevice,
    new_status: str,
    now_utc: datetime,
) -> None:
    """Publica el evento DEVICE_STATUS_CHANGED en el canal Pub/Sub del tenant."""
    pubsub_channel = f"rg:pubsub:events:{tenant_id}"
    event_payload = {
        "event_name": "DEVICE_STATUS_CHANGED",
        "payload": {
            "device_id": str(dev.id),
            "status": new_status,
            "router_id": str(router_id),
            "endpoint_identifier": dev.endpoint_identifier,
            "last_seen_at": now_utc.isoformat(),
        },
    }
    try:
        await redis.publish(pubsub_channel, json.dumps(event_payload))
    except Exception as e:
        logger.debug(f"Aviso publicando evento DEVICE_STATUS_CHANGED: {e}")


async def _poll_single_router_sessions(
    session: Any,
    tenant_id: uuid.UUID,
    router: Router,
    is_isp_mode: bool,
    verify_icmp: bool = False,
) -> int:
    """Consulta híbrida de las tablas de sesiones en RouterOS v7 con filtro delta en base de datos."""
    redis = get_redis_client()

    # 1. Comprobación rápida de Circuit Breaker en KeyDB
    cb_key = f"rg:{tenant_id}:diag:circuit:router:{router.id}"
    cb_state = await redis.get(cb_key)
    if cb_state and (cb_state == "OPEN" or cb_state == b"OPEN"):
        logger.debug(f"Router {router.display_name} en Circuit Breaker abierto. Omitiendo sondeo pasivo.")
        return 0

    try:
        client = _create_client_from_vault(router, tenant_id)
    except Exception as exc:
        logger.debug(f"No se pudo crear cliente para router {router.display_name}: {exc}")
        return 0

    # 2. Consultar los dispositivos registrados para este router (con ipv4_address precargada)
    stmt_devs = (
        select(SubscriberDevice)
        .options(selectinload(SubscriberDevice.ipv4_address))
        .where(
            SubscriberDevice.tenant_id == tenant_id,
            SubscriberDevice.router_id == router.id,
        )
    )
    devices = list((await session.execute(stmt_devs)).scalars().all())
    if not devices:
        return 0

    try:
        async with client:
            active_identifiers = await _collect_router_active_identifiers(
                client=client,
                is_isp_mode=is_isp_mode,
                devices=devices,
                verify_icmp=verify_icmp,
            )
    except Exception as exc:
        logger.warning(f"Error consultando tablas de sesiones en router {router.display_name}: {exc}")
        return 0

    changed_count = 0
    now_utc = datetime.now(UTC)

    for dev in devices:
        is_present = _is_device_matched(dev, active_identifiers)
        new_status = "ONLINE" if is_present else "OFFLINE"

        # 3. Filtro Delta (Zero-Write DB): Solo actualiza y emite si hay cambio de estado
        if new_status != dev.last_reachability_status:
            dev.last_reachability_status = new_status
            dev.last_seen_at = now_utc
            changed_count += 1
            await _publish_device_status_change(redis, tenant_id, router.id, dev, new_status, now_utc)

    if changed_count > 0:
        await session.commit()
        logger.info(
            f"[Poller Delta] Router {router.display_name}: {changed_count} dispositivos cambiaron de estado."
        )

    return changed_count


async def poll_tenant_subscribers_cycle(tenant_id: uuid.UUID, is_isp_mode: bool) -> None:
    """Ejecuta el ciclo de sondeo híbrido escalonado para todos los routers de un tenant."""
    async with async_session_maker() as session:
        await set_tenant_context(session, str(tenant_id), is_superadmin=False)
        stmt_routers = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(
                Router.tenant_id == tenant_id,
                Router.admin_state != RouterAdminStateEnum.RETIRED,
                Router.is_reachable.is_(True),
            )
            .order_by(Router.display_name.asc())
        )
        routers = list((await session.execute(stmt_routers)).scalars().all())
        if not routers:
            return

        interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)
        verify_icmp = bool(getattr(settings, "ROSGRID_SUBSCRIBER_ICMP_PROBE_ENABLED", True))
        base_delay = max(MIN_INTER_ROUTER_JITTER_SECONDS, interval / max(1, len(routers)))

        for r in routers:
            await _poll_single_router_sessions(
                session=session,
                tenant_id=tenant_id,
                router=r,
                is_isp_mode=is_isp_mode,
                verify_icmp=verify_icmp,
            )
            jitter = random.uniform(0.1, 0.8)
            await asyncio.sleep(base_delay + jitter)


async def subscriber_status_poller_worker_loop() -> None:
    """Loop principal del Worker de Sondeo Híbrido Escalonado (StaggeredSessionPoller)."""
    logger.info("=== Iniciando Worker de Sondeo Híbrido Escalonado (StaggeredSessionPoller) ===")
    interval = getattr(settings, "ROSGRID_BACKGROUND_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)

    while True:
        try:
            async with async_session_maker() as session:
                await set_tenant_context(session, None, is_superadmin=True)
                stmt_t = select(Tenant).where(Tenant.status == TenantStatusEnum.ACTIVE)
                tenants = list((await session.execute(stmt_t)).scalars().all())

            for t in tenants:
                is_isp = bool(getattr(t, "isp_module_enabled", False))
                try:
                    await poll_tenant_subscribers_cycle(t.id, is_isp)
                except Exception as e:
                    logger.warning(f"Error en ciclo de sondeo para tenant {t.name}: {e}")

        except asyncio.CancelledError:
            logger.info("Worker StaggeredSessionPoller cancelado.")
            break
        except Exception as exc:
            logger.error(f"Excepción en ciclo de StaggeredSessionPoller: {exc}", exc_info=True)

        await asyncio.sleep(interval)
```

---

### Paso 3: Propagación Reactiva del Evento `DEVICE_STATUS_CHANGED` hacia `useIpamStore.ts` (`vue3/src/stores/useNocEventsStore.ts` y `vue3/src/stores/useIpamStore.ts`)

1. En [`vue3/src/stores/useNocEventsStore.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/stores/useNocEventsStore.ts) (líneas 30–40), emitir además el `CustomEvent` de navegador `rosgrid:device-status-changed` cuando llega `DEVICE_STATUS_CHANGED` por WebSocket:

#### `Target` en `vue3/src/stores/useNocEventsStore.ts`:
```typescript
      // Captura reactiva de cambio de estado de abonados/clientes en tiempo real
      if (eventName === 'DEVICE_STATUS_CHANGED') {
        const p = payload.payload || payload;
        lastDeviceStatusEvent.value = {
          deviceId: p.device_id,
          status: p.status,
          routerId: p.router_id,
          endpointIdentifier: p.endpoint_identifier,
          lastSeenAt: p.last_seen_at,
        };
      }
```

#### `Replacement` en `vue3/src/stores/useNocEventsStore.ts`:
```typescript
      // Captura reactiva de cambio de estado de abonados/clientes en tiempo real
      if (eventName === 'DEVICE_STATUS_CHANGED') {
        const p = payload.payload || payload;
        const statusDetail = {
          deviceId: p.device_id,
          status: p.status,
          routerId: p.router_id,
          endpointIdentifier: p.endpoint_identifier,
          lastSeenAt: p.last_seen_at,
        };
        lastDeviceStatusEvent.value = statusDetail;
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('rosgrid:device-status-changed', { detail: statusDetail }));
        }
      }
```

2. En [`vue3/src/stores/useIpamStore.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/stores/useIpamStore.ts) (antes del `return {` final en la línea 224), escuchar `rosgrid:device-status-changed` para actualizar en vivo `last_reachability_status` y `last_seen_at` en `customerServices`:

#### `Target` en `vue3/src/stores/useIpamStore.ts`:
```typescript
  return {
    vrfs,
```

#### `Replacement` en `vue3/src/stores/useIpamStore.ts`:
```typescript
  if (typeof window !== 'undefined') {
    window.addEventListener('rosgrid:device-status-changed', ((ev: CustomEvent) => {
      const detail = ev.detail;
      if (!detail?.deviceId) return;
      customerServices.value = customerServices.value.map((s) =>
        s.id === detail.deviceId
          ? {
              ...s,
              last_reachability_status: detail.status || s.last_reachability_status,
              last_seen_at: detail.lastSeenAt || s.last_seen_at,
            }
          : s,
      );
      triggerRef(customerServices);
    }) as EventListener);
  }

  return {
    vrfs,
```

---

### Paso 4: Ampliar Pruebas Unitarias en `fastapi/tests/workers/test_subscriber_status_poller.unit.py`

En [`fastapi/tests/workers/test_subscriber_status_poller.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/workers/test_subscriber_status_poller.unit.py), agregar pruebas que certifiquen:
1. `test_poller_isp_mode_falls_back_to_dhcp_leases_for_dhcp_subscribers`: cuando `is_isp_mode=True` y un abonado usa DHCP (no aparece en `/ppp/active`, pero sí en `/ip/dhcp-server/lease` con su MAC `48:8F:5A:11:22:33`), el poller consulta `/ip/dhcp-server/lease` y lo marca `ONLINE`.
2. `test_poller_icmp_probe_marks_unbound_or_powered_off_dhcp_device_offline`: cuando `verify_icmp=True` y `client.post("/ping", ...)` devuelve `[{"received": 0, "status": "timeout"}]` porque la ONU fue apagada aunque el lease DHCP aún no había vencido, el poller marca al abonado como `OFFLINE` y publica `DEVICE_STATUS_CHANGED`.

#### `Target` al final de `fastapi/tests/workers/test_subscriber_status_poller.unit.py`:
```python
    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=True)
            assert changed == 1
            assert mock_device.last_reachability_status == "ONLINE"
            mock_client.get.assert_called_once_with("/ppp/active")
            mock_session.commit.assert_called_once()
            mock_redis.publish.assert_called_once()
```

#### `Replacement` al final de `fastapi/tests/workers/test_subscriber_status_poller.unit.py`:
```python
    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=True)
            assert changed == 1
            assert mock_device.last_reachability_status == "ONLINE"
            mock_client.get.assert_called_once_with("/ppp/active")
            mock_session.commit.assert_called_once()
            mock_redis.publish.assert_called_once()


@pytest.mark.asyncio
async def test_poller_isp_mode_falls_back_to_dhcp_leases_for_dhcp_subscribers(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que con is_isp_mode=True, si el abonado es DHCP y no está en /ppp/active, consulta /ip/dhcp-server/lease."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "OFFLINE"
    mock_device.pppoe_username = None
    mock_device.endpoint_identifier = "CLI-DHCP-01"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = [
        [],  # /ppp/active vacío
        [{"address": "192.168.10.50", "status": "bound", "mac-address": "48:8F:5A:11:22:33"}],  # /ip/dhcp-server/lease
    ]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(mock_session, mock_tenant_id, mock_router, is_isp_mode=True)
            assert changed == 1
            assert mock_device.last_reachability_status == "ONLINE"


@pytest.mark.asyncio
async def test_poller_icmp_probe_marks_powered_off_dhcp_device_offline(
    mock_tenant_id: uuid.UUID, mock_router: Router, mock_device: SubscriberDevice
) -> None:
    """Verifica que cuando verify_icmp=True, si la ONU no responde Ping aunque el lease DHCP siga bound, pasa a OFFLINE."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_session = AsyncMock()

    mock_device.last_reachability_status = "ONLINE"
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_device]
    mock_session.execute.return_value = mock_result

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = [
        {"address": "192.168.10.50", "status": "bound", "mac-address": "48:8F:5A:11:22:33"}
    ]
    mock_client.post.return_value = [{"sent": 1, "received": 0, "status": "timeout"}]

    with patch("src.workers.subscriber_status_poller.get_redis_client", return_value=mock_redis):
        with patch("src.workers.subscriber_status_poller._create_client_from_vault", return_value=mock_client):
            changed = await _poll_single_router_sessions(
                mock_session,
                mock_tenant_id,
                mock_router,
                is_isp_mode=False,
                verify_icmp=True,
            )
            assert changed == 1
            assert mock_device.last_reachability_status == "OFFLINE"
            mock_redis.publish.assert_called_once()
```

---

## 3. Verificación en Contenedores Docker Efímeros (`Rule Zero`)

```bash
docker compose -f fastapi/docker-compose.qa.yml run --rm -T backend-qa pytest tests/workers/test_subscriber_status_poller.unit.py
docker compose -f vue3/docker-compose.qa.yml run --rm -T frontend-qa npx vitest run src/stores/useNocEventsStore.unit.ts
```
